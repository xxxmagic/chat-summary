<?php
// ─── Config ───────────────────────────────────────────────────────────────────

session_start();

function loadEnv($path) {
    if (!file_exists($path)) return;
    foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#' || strpos($line, '=') === false) continue;
        [$k, $v] = explode('=', $line, 2);
        putenv(trim($k) . '=' . trim($v));
    }
}

loadEnv(dirname(__DIR__, 3) . '/chat-summary/.env');

define('GROK_API_KEY',    getenv('GROK_API_KEY')    ?: '');
define('GROK_BASE_URL',   getenv('GROK_BASE_URL')   ?: 'https://api.x.ai/v1');
define('GROK_MODEL',      getenv('GROK_MODEL')      ?: 'grok-4-1-fast-non-reasoning');
define('CHUNK_SIZE',      (int)(getenv('SUMMARY_CHUNK_SIZE')                ?: 10));
define('MAX_FIELDS',      (int)(getenv('SUMMARY_MAX_FIELDS_PER_CATEGORY')   ?: 5));
define('MAX_LIST',        (int)(getenv('SUMMARY_MAX_LIST_ITEMS')            ?: 4));
define('MAX_VAL_LEN',     (int)(getenv('SUMMARY_MAX_VALUE_LENGTH')          ?: 120));

$DATA_DIR       = dirname(__DIR__, 3) . '/chat-summary/data';
$DIALOGUES_FILE = $DATA_DIR . '/dialogues.json';

// ─── Routing ──────────────────────────────────────────────────────────────────

$uri    = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$uri    = rtrim($uri, '/');
$method = $_SERVER['REQUEST_METHOD'];

// Strip base path if app lives in a subdirectory
$base = rtrim(dirname($_SERVER['SCRIPT_NAME']), '/');
if ($base !== '' && strpos($uri, $base) === 0) {
    $uri = substr($uri, strlen($base));
}
if ($uri === '') $uri = '/';

// Serve static files (css/js) directly if running via PHP built-in server
if (preg_match('#^/static/.+\.(css|js|map)$#', $uri)) {
    $file = __DIR__ . $uri;
    if (file_exists($file)) {
        $ext = pathinfo($file, PATHINFO_EXTENSION);
        $mime = ['css' => 'text/css', 'js' => 'application/javascript'][$ext] ?? 'text/plain';
        header('Content-Type: ' . $mime);
        readfile($file);
        exit;
    }
}

// ─── JSON helpers ─────────────────────────────────────────────────────────────

function jsonOut($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function getBody() {
    static $body = null;
    if ($body === null) $body = json_decode(file_get_contents('php://input'), true) ?? [];
    return $body;
}

// ─── Data loaders ─────────────────────────────────────────────────────────────

function loadDialogues() {
    global $DIALOGUES_FILE;
    static $cache = null;
    if ($cache !== null) return $cache;
    if (!file_exists($DIALOGUES_FILE)) return ($cache = []);
    $raw  = json_decode(file_get_contents($DIALOGUES_FILE), true);
    $byId = [];
    foreach (($raw['dialogues'] ?? []) as $d) {
        $byId[$d['dialogue_id']] = $d;
    }
    return ($cache = $byId);
}

function getDialogueList() {
    $list = [];
    foreach (loadDialogues() as $id => $d) {
        $list[] = [
            'dialogue_id'               => $id,
            'dialogue_length_messages'  => $d['dialogue_length_messages'],
            'dialogue_length_chars'     => $d['dialogue_length_chars'] ?? 0,
        ];
    }
    return $list;
}

function getMessages($dialogueId, $lang = 'sv') {
    $dialogues = loadDialogues();
    if (!isset($dialogues[$dialogueId])) return [];
    $msgs = $dialogues[$dialogueId]['messages'][$lang]
         ?? $dialogues[$dialogueId]['messages']['sv']
         ?? [];
    return $msgs;
}

// ─── Summaries (session-only, no disk writes) ─────────────────────────────────

function defaultSummary() {
    $cat = ['identity' => [], 'work_money' => [], 'lifestyle' => [],
            'relationship' => [], 'sexual' => [], 'personality' => []];
    return ['users' => ['user' => $cat, 'persona' => $cat]];
}

function countFacts($node) {
    if (is_array($node)) {
        $n = 0;
        foreach ($node as $v) $n += countFacts($v);
        return $n;
    }
    if ($node === null) return 0;
    if (is_string($node)) return trim($node) !== '' ? 1 : 0;
    return 1;
}

function getSummaryState($dialogueId) {
    $dialogues = loadDialogues();
    $total = isset($dialogues[$dialogueId])
        ? $dialogues[$dialogueId]['dialogue_length_messages']
        : 0;

    $entry   = $_SESSION['summaries'][(string)$dialogueId] ?? null;

    if (!$entry) {
        $summary = defaultSummary();
        return [
            'dialogue_id'        => $dialogueId,
            'processed_messages' => 0,
            'total_messages'     => $total,
            'is_complete'        => false,
            'summary'            => $summary,
            'fact_count'         => countFacts($summary),
            'updated_at'         => null,
        ];
    }

    $summary   = $entry['summary'] ?? defaultSummary();
    $processed = $entry['processed_messages'] ?? 0;
    return [
        'dialogue_id'        => $dialogueId,
        'processed_messages' => $processed,
        'total_messages'     => $total,
        'is_complete'        => $processed >= $total,
        'summary'            => $summary,
        'fact_count'         => countFacts($summary),
        'updated_at'         => $entry['updated_at'] ?? null,
    ];
}

function saveSummaryState($dialogueId, $processed, $summary) {
    if (!isset($_SESSION['summaries'])) $_SESSION['summaries'] = [];
    $_SESSION['summaries'][(string)$dialogueId] = [
        'processed_messages' => $processed,
        'summary'            => $summary,
        'updated_at'         => date('c'),
    ];
}

// ─── Summary sanitizer ────────────────────────────────────────────────────────

$KEY_WEIGHTS = [
    'identity'     => ['name'=>6,'names'=>6,'age'=>5,'city'=>4.5,'country'=>4.5,'phone'=>6,'email'=>6,'kik'=>5.5,'telegram'=>5.5,'whatsapp'=>5.5],
    'relationship' => ['status'=>6,'partner'=>5.5,'married'=>5,'single'=>5,'children'=>4],
    'work_money'   => ['work'=>4.5,'job'=>4.5,'occupation'=>4.5,'income'=>4,'financial'=>4],
    'lifestyle'    => ['location'=>4.5,'hobbies'=>3.5],
    'sexual'       => ['orientation'=>5,'interests'=>4.5,'boundaries'=>5,'preferences'=>4.5],
    'personality'  => ['traits'=>4.5,'temperament'=>4],
];

function scalarImportance($val) {
    if ($val === null) return -10;
    $low = ['','unknown','n/a','na','none','null','?','-','no info','not sure'];
    if (is_bool($val)) return 0.8;
    if (is_numeric($val)) return 1.0;
    $t = trim((string)$val);
    if (!$t) return -10;
    if (in_array(strtolower($t), $low)) return -8;
    $s = 1.0;
    if (preg_match('/\d/', $t)) $s += 0.6;
    if (strpos($t, '@') !== false) $s += 0.8;
    $l = mb_strlen($t);
    if ($l >= 4 && $l <= 80) $s += 0.4;
    if ($l > 120) $s -= 0.4;
    return $s;
}

function valueImportance($val) {
    if (is_array($val)) {
        if (empty($val)) return -10;
        $scores = array_filter(array_map('valueImportance', $val), function($s) { return $s > -9; });
        if (!$scores) return -10;
        rsort($scores);
        return 0.7 + array_sum(array_slice($scores, 0, 3));
    }
    return scalarImportance($val);
}

function keyImportance($category, $key) {
    global $KEY_WEIGHTS;
    $k = strtolower(trim($key));
    $base = 0.5 + ($KEY_WEIGHTS[$category][$k] ?? 0);
    foreach (['name','phone','email','kik','city','status'] as $token) {
        if (strpos($k, $token) !== false) { $base += 1.0; break; }
    }
    if (mb_strlen($k) <= 2) $base -= 0.4;
    return $base;
}

function sanitizeScalar($val) {
    if ($val === null || is_bool($val) || is_numeric($val)) return $val;
    $t = trim((string)$val);
    return mb_strlen($t) > MAX_VAL_LEN ? mb_substr($t, 0, MAX_VAL_LEN - 1) . '…' : $t;
}

function sanitizeValue($val) {
    if (is_array($val) && array_keys($val) !== range(0, count($val)-1)) {
        // associative = object
        return sanitizeMapping($val, MAX_FIELDS);
    }
    if (is_array($val)) {
        // list
        $out = []; $seen = [];
        foreach (array_slice($val, 0, MAX_LIST) as $item) {
            $n = sanitizeValue($item);
            if ($n === null || $n === '' || $n === [] || $n === []) continue;
            $m = json_encode($n, JSON_UNESCAPED_UNICODE);
            if (in_array($m, $seen)) continue;
            $seen[] = $m;
            $out[]  = $n;
        }
        return $out;
    }
    return sanitizeScalar($val);
}

function sanitizeMapping($map, $maxFields, $category = null) {
    $scored = [];
    foreach ($map as $k => $v) {
        $k = trim((string)$k);
        if (!$k) continue;
        $n = sanitizeValue($v);
        if ($n === null || $n === '' || $n === []) continue;
        $score = keyImportance($category ?? '', $k) + valueImportance($n);
        $scored[] = [$score, $k, $n];
    }
    usort($scored, function($a, $b) { return $b[0] <=> $a[0]; });
    $out = [];
    foreach ($scored as [$score, $k, $n]) {
        if (count($out) >= $maxFields) break;
        if ($score <= -5) continue;
        $out[$k] = $n;
    }
    return $out;
}

function applySummaryLimits($obj) {
    $result  = defaultSummary();
    $usersIn = $obj['users'] ?? [];
    $cats    = ['identity','work_money','lifestyle','relationship','sexual','personality'];
    foreach (['user','persona'] as $person) {
        $personIn = $usersIn[$person] ?? [];
        foreach ($cats as $cat) {
            $catIn = $personIn[$cat] ?? [];
            $result['users'][$person][$cat] = is_array($catIn)
                ? sanitizeMapping($catIn, MAX_FIELDS, $cat)
                : [];
        }
    }
    return $result;
}

// ─── Prompts ──────────────────────────────────────────────────────────────────

$LANG_INSTRUCTIONS = [
    'ru' => 'Write all field VALUES in Russian.',
    'en' => 'Write all field VALUES in English.',
    'sv' => 'Write all field VALUES in Swedish.',
];

function defaultSystemPrompt() {
    $schema = json_encode(defaultSummary(), JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    return "You are an intelligence analyst building a factual profile of a person from a chat conversation.\n"
        . "Your goal is NOT to summarize the conversation — your goal is to EXTRACT specific facts.\n\n"
        . "Return ONLY valid JSON with this exact schema:\n$schema\n\n"
        . "ROLES — strictly one person each:\n"
        . "- users.user = the CLIENT: the real person who initiated contact\n"
        . "- users.persona = the OPERATOR character: the person being played by the operator\n"
        . "Determine roles from context. Keep them strictly separate — never mix.\n\n"
        . "WHAT TO LOOK FOR in each category:\n"
        . "- identity: name, age, city, country, contact handles (phone, kik, telegram, email)\n"
        . "- work_money: job title, employer, income level, financial situation, debts\n"
        . "- lifestyle: living situation (alone/family), daily schedule, hobbies, interests\n"
        . "- relationship: marital status, partner, ex-partners, children, family situation\n"
        . "- sexual: expressed desires, preferences, boundaries, orientation\n"
        . "- personality: emotional state, communication style, red flags, manipulation tactics\n\n"
        . "Language: {lang}\n\n"
        . "Rules:\n"
        . "- Only record facts explicitly stated or strongly implied — no guessing.\n"
        . "- Preserve existing facts unless directly contradicted.\n"
        . "- Each category = max 1-2 concise facts. No long prose.\n"
        . "- identity.gender must be a single word: female or male.\n"
        . "- Skip a category entirely if nothing is known — use empty object.\n"
        . "- Respond with pure JSON only.";
}

function defaultUserPrompt() {
    return "Extract and update profile facts from the new messages below.\n"
        . "Focus on finding real facts about the client: family, work, location, finances, relationships.\n\n"
        . "previous_summary:\n{previous_summary}\n\nnew_messages:\n{new_messages}";
}

// ─── Grok API ─────────────────────────────────────────────────────────────────

function callGrok($prevSummary, $newMessages, $systemPrompt, $userPrompt, $lang) {
    global $LANG_INSTRUCTIONS;

    $langInstr = $LANG_INSTRUCTIONS[$lang] ?? "Write all field VALUES in $lang.";

    $systemPrompt = str_replace('{lang}', $langInstr, $systemPrompt);
    $userPrompt   = str_replace('{lang}', $langInstr, $userPrompt);

    $limitsNote = "\nHard limits — strictly enforce:\n"
        . "- max " . MAX_FIELDS    . " fields per category\n"
        . "- max " . MAX_LIST      . " items in any array\n"
        . "- max " . MAX_VAL_LEN   . " chars per value\n"
        . "- Each category = 1-2 line note only. Drop low-signal facts.";
    if (strpos($systemPrompt, 'Hard limits') === false) {
        $systemPrompt .= $limitsNote;
    }

    $userPrompt = str_replace(
        ['{previous_summary}', '{new_messages}'],
        [
            json_encode($prevSummary, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
            json_encode($newMessages, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT),
        ],
        $userPrompt
    );

    $payload = json_encode([
        'model'           => GROK_MODEL,
        'temperature'     => 0.1,
        'response_format' => ['type' => 'json_object'],
        'messages'        => [
            ['role' => 'system', 'content' => $systemPrompt],
            ['role' => 'user',   'content' => $userPrompt],
        ],
    ], JSON_UNESCAPED_UNICODE);

    $ch = curl_init(rtrim(GROK_BASE_URL, '/') . '/chat/completions');
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST           => true,
        CURLOPT_POSTFIELDS     => $payload,
        CURLOPT_TIMEOUT        => 120,
        CURLOPT_HTTPHEADER     => [
            'Authorization: Bearer ' . GROK_API_KEY,
            'Content-Type: application/json',
        ],
    ]);
    $resp   = curl_exec($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err    = curl_error($ch);
    curl_close($ch);

    if ($err) throw new RuntimeException("curl error: $err");
    if ($status !== 200) throw new RuntimeException("Grok API $status: $resp");

    $data    = json_decode($resp, true);
    $content = $data['choices'][0]['message']['content'] ?? '';
    $content = trim($content);

    // Extract JSON block if wrapped in text
    if ($content[0] !== '{') {
        $start = strpos($content, '{');
        $end   = strrpos($content, '}');
        if ($start !== false && $end > $start)
            $content = substr($content, $start, $end - $start + 1);
    }

    $parsed = json_decode($content, true);
    if ($parsed === null) {
        // Light repair: remove trailing commas
        $content = preg_replace('/,\s*([\}\]])/', '$1', $content);
        $parsed  = json_decode($content, true);
        if ($parsed === null) throw new RuntimeException("Invalid JSON from model: " . substr($content, 0, 200));
    }

    return applySummaryLimits($parsed);
}

// ─── Route handlers ───────────────────────────────────────────────────────────

// GET /
if ($uri === '/' || $uri === '/index.php') {
    include __DIR__ . '/templates/index.html';
    exit;
}

// GET /api/status
if ($uri === '/api/status' && $method === 'GET') {
    jsonOut([
        'dialogues_ready' => count(loadDialogues()) > 0,
        'dialogue_count'  => count(loadDialogues()),
        'chunk_size'      => CHUNK_SIZE,
    ]);
}

// GET /api/dialogues
if ($uri === '/api/dialogues' && $method === 'GET') {
    jsonOut(getDialogueList());
}

// GET /api/summaries
if ($uri === '/api/summaries' && $method === 'GET') {
    $states = array_map(function($d) { return getSummaryState($d['dialogue_id']); }, getDialogueList());
    jsonOut($states);
}

// Match /api/dialogues/{id}/...
if (preg_match('#^/api/dialogues/(\d+)(/.*)?$#', $uri, $m)) {
    $dialogueId = (int)$m[1];
    $sub        = $m[2] ?? '';

    // GET /api/dialogues/{id}/messages
    if ($sub === '/messages' && $method === 'GET') {
        $lang  = $_GET['lang'] ?? 'sv';
        $limit = isset($_GET['limit']) ? (int)$_GET['limit'] : null;
        $msgs  = getMessages($dialogueId, $lang);
        $total = count($msgs);
        $serveLang = $lang;
        // fallback check
        $dialogues = loadDialogues();
        if (isset($dialogues[$dialogueId]) && !isset($dialogues[$dialogueId]['messages'][$lang])) {
            $serveLang = 'sv';
        }
        if ($limit) $msgs = array_slice($msgs, 0, $limit);
        jsonOut([
            'dialogue_id'       => $dialogueId,
            'total_messages'    => $total,
            'returned_messages' => count($msgs),
            'lang'              => $serveLang,
            'messages'          => array_values($msgs),
        ]);
    }

    // GET /api/dialogues/{id}/summary
    if ($sub === '/summary' && $method === 'GET') {
        jsonOut(getSummaryState($dialogueId));
    }

    // POST /api/dialogues/{id}/summary/reset
    if ($sub === '/summary/reset' && $method === 'POST') {
        saveSummaryState($dialogueId, 0, defaultSummary());
        jsonOut(getSummaryState($dialogueId));
    }

    // POST /api/dialogues/{id}/summary/next
    if ($sub === '/summary/next' && $method === 'POST') {
        $state = getSummaryState($dialogueId);
        if ($state['is_complete']) {
            jsonOut(array_merge($state, ['processed_in_this_step' => 0, 'status' => 'already_complete']));
        }

        $allMsgs = getMessages($dialogueId, 'sv');
        $offset  = $state['processed_messages'];
        $chunk   = array_slice($allMsgs, $offset, CHUNK_SIZE);

        if (!$chunk) {
            jsonOut(array_merge($state, ['processed_in_this_step' => 0, 'status' => 'no_new_messages']));
        }

        $body         = getBody();
        $systemPrompt = trim($body['system_prompt'] ?? '') ?: (trim($_COOKIE['chat_prompt_system'] ?? '') ?: defaultSystemPrompt());
        $userPrompt   = trim($body['user_prompt']   ?? '') ?: (trim($_COOKIE['chat_prompt_user']   ?? '') ?: defaultUserPrompt());
        $lang         = $body['lang'] ?? 'en';

        try {
            $updated = callGrok($state['summary'], array_values($chunk), $systemPrompt, $userPrompt, $lang);
        } catch (Exception $e) {
            jsonOut(['error' => $e->getMessage(), 'status' => 'summary_failed'], 500);
        }

        $newProcessed = $offset + count($chunk);
        saveSummaryState($dialogueId, $newProcessed, $updated);
        $newState = getSummaryState($dialogueId);
        jsonOut(array_merge($newState, ['processed_in_this_step' => count($chunk), 'status' => 'updated']));
    }
}

// 404
jsonOut(['error' => 'Not found', 'path' => $uri], 404);
