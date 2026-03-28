<?php
session_start();
require_once __DIR__ . '/prompts_config.php';

// ─── Lang switching (must be before any output) ───────────────────────────────

if (isset($_GET['lang']) && in_array($_GET['lang'], ['ru','en','sv']) && $_SERVER['REQUEST_METHOD'] === 'GET') {
    setcookie('chat_lang', $_GET['lang'], ['expires' => time() + 365*24*3600, 'path' => '/']);
    $qs = isset($_GET['saved']) ? '?saved=1' : '';
    header('Location: prompts.php' . $qs);
    exit;
}

// ─── Lang (from cookie, default ru) ──────────────────────────────────────────

$lang = $_COOKIE['chat_lang'] ?? 'ru';
if (!in_array($lang, ['ru', 'en', 'sv'])) $lang = 'ru';

// ─── Translations ─────────────────────────────────────────────────────────────

$T = [
  'ru' => [
    'title'        => 'Промпты для Grok',
    'page_title'   => 'Промпты — Chat Summary',
    'back'         => '← Назад к чатам',
    'saved'        => '✓ Сохранено',
    'modified'     => 'Изменён',
    'label_system' => 'System prompt',
    'label_user'   => 'User prompt',
    'hint_system'  => 'Плейсхолдер: {lang} — язык ответа (ru / en / sv)',
    'hint_user'    => 'Плейсхолдеры: {previous_summary}, {new_messages}, {lang}',
    'btn_save'     => 'Сохранить',
    'btn_reset'    => 'Сбросить на дефолт',
    'confirm_reset'=> 'Сбросить промпты на дефолт?',
    'btn_back'     => '← Назад',
  ],
  'en' => [
    'title'        => 'Grok Prompts',
    'page_title'   => 'Prompts — Chat Summary',
    'back'         => '← Back to chats',
    'saved'        => '✓ Saved',
    'modified'     => 'Modified',
    'label_system' => 'System prompt',
    'label_user'   => 'User prompt',
    'hint_system'  => 'Placeholder: {lang} — response language (ru / en / sv)',
    'hint_user'    => 'Placeholders: {previous_summary}, {new_messages}, {lang}',
    'btn_save'     => 'Save',
    'btn_reset'    => 'Reset to default',
    'confirm_reset'=> 'Reset prompts to default?',
    'btn_back'     => '← Back',
  ],
  'sv' => [
    'title'        => 'Grok-promptar',
    'page_title'   => 'Promptar — Chat Summary',
    'back'         => '← Tillbaka till chattar',
    'saved'        => '✓ Sparad',
    'modified'     => 'Ändrad',
    'label_system' => 'Systemprompt',
    'label_user'   => 'Användarprompt',
    'hint_system'  => 'Platshållare: {lang} — svarsspråk (ru / en / sv)',
    'hint_user'    => 'Platshållare: {previous_summary}, {new_messages}, {lang}',
    'btn_save'     => 'Spara',
    'btn_reset'    => 'Återställ standard',
    'confirm_reset'=> 'Återställa promptar till standard?',
    'btn_back'     => '← Tillbaka',
  ],
];

function t($key) {
    global $T, $lang;
    return $T[$lang][$key] ?? $T['en'][$key] ?? $key;
}

$cookieOpts = ['expires' => time() + 30 * 24 * 3600, 'path' => '/'];

// ─── Handle POST ──────────────────────────────────────────────────────────────

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    if ($action === 'reset') {
        setcookie('chat_prompt_system', '', array_merge($cookieOpts, ['expires' => 1]));
        setcookie('chat_prompt_user',   '', array_merge($cookieOpts, ['expires' => 1]));
    } else {
        $sys  = trim($_POST['system_prompt'] ?? '');
        $user = trim($_POST['user_prompt']   ?? '');
        setcookie('chat_prompt_system', $sys,  $cookieOpts);
        setcookie('chat_prompt_user',   $user, $cookieOpts);
    }
    header('Location: prompts.php?saved=1');
    exit;
}

// ─── Load current values ──────────────────────────────────────────────────────

$systemPrompt = $_COOKIE['chat_prompt_system'] ?? '';
$userPrompt   = $_COOKIE['chat_prompt_user']   ?? '';
$isCustom     = ($systemPrompt !== '' || $userPrompt !== '');
if (!$systemPrompt) $systemPrompt = defaultSystemPrompt();
if (!$userPrompt)   $userPrompt   = defaultUserPrompt();

$saved = isset($_GET['saved']);

function esc($s) { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
?>
<!doctype html>
<html lang="<?= esc($lang) ?>">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title><?= esc(t('page_title')) ?></title>
  <link rel="stylesheet" href="static/styles.css?v=37" />
  <style>
    .prompts-page { max-width: 960px; margin: 0 auto; padding-bottom: 48px; }
    .prompts-nav {
      display: flex; align-items: center; gap: 12px;
      margin-bottom: 32px; flex-wrap: wrap;
    }
    .prompts-nav h1 { margin: 0; font-size: 22px; flex: 1; }
    .lang-switcher { display: flex; gap: 4px; }
    .saved-badge {
      background: #d1fae5; color: #065f46;
      border: 1px solid #a7f3d0; border-radius: 6px;
      padding: 5px 14px; font-size: 13px; font-weight: 600;
    }
    .modified-badge {
      background: #fef3c7; color: #92400e;
      border: 1px solid #fde68a; border-radius: 6px;
      padding: 5px 14px; font-size: 13px;
    }
    .prompt-block { margin-bottom: 32px; }
    .prompt-label {
      display: block; font-size: 12px; font-weight: 700;
      letter-spacing: 0.07em; text-transform: uppercase;
      color: #6b7280; margin-bottom: 10px;
    }
    .prompt-textarea {
      width: 100%; box-sizing: border-box;
      min-height: 280px; padding: 18px 20px;
      font-family: "JetBrains Mono","Fira Code","Cascadia Code","Consolas",monospace;
      font-size: 13.5px; line-height: 1.75; color: #111827;
      background: #ffffff; border: 1.5px solid #d1d5db;
      border-radius: 10px; resize: vertical; outline: none;
    }
    .prompt-textarea--large { min-height: 560px; }
      transition: border-color .15s;
    }
    .prompt-textarea:focus { border-color: #1f2937; box-shadow: 0 0 0 3px rgba(31,41,55,.08); }
    .hint-code {
      font-size: 12px; color: #9ca3af; margin-top: 8px;
    }
    .hint-code code {
      background: #f3f4f6; border-radius: 4px; padding: 1px 5px;
      font-family: monospace; font-size: 11.5px; color: #374151;
    }
    .form-actions {
      display: flex; gap: 10px; flex-wrap: wrap;
      padding-top: 24px; border-top: 1px solid #e5e7eb;
    }
    .btn-link {
      padding: 8px 16px; border-radius: 6px; border: 1px solid #d1d5db;
      text-decoration: none; color: #374151; font-size: 14px;
      background: #fff; cursor: pointer; line-height: 1.4;
    }
    .btn-link:hover { border-color: #9ca3af; }
  </style>
</head>
<body>
<main>
  <div class="prompts-page">
    <div class="prompts-nav">
      <h1><?= esc(t('title')) ?></h1>
      <?php if ($saved): ?>
        <span class="saved-badge"><?= esc(t('saved')) ?></span>
      <?php endif; ?>
      <?php if ($isCustom && !$saved): ?>
        <span class="modified-badge"><?= esc(t('modified')) ?></span>
      <?php endif; ?>
      <div class="lang-switcher">
        <?php foreach (['sv','ru','en'] as $l): ?>
          <a href="?lang=<?= $l ?>" class="lang-btn <?= $l === $lang ? 'active' : '' ?>"
             style="text-decoration:none"><?= strtoupper($l) ?></a>
        <?php endforeach; ?>
      </div>
      <a href="./" class="btn-link"><?= esc(t('back')) ?></a>
    </div>

    <form method="POST">
      <div class="prompt-block">
        <label class="prompt-label" for="system_prompt"><?= esc(t('label_system')) ?></label>
        <textarea id="system_prompt" name="system_prompt" class="prompt-textarea prompt-textarea--large"
                  spellcheck="false"><?= esc($systemPrompt) ?></textarea>
        <p class="hint-code"><?= esc(t('hint_system')) ?></p>
      </div>

      <div class="prompt-block">
        <label class="prompt-label" for="user_prompt"><?= esc(t('label_user')) ?></label>
        <textarea id="user_prompt" name="user_prompt" class="prompt-textarea"
                  spellcheck="false"><?= esc($userPrompt) ?></textarea>
        <p class="hint-code"><?= esc(t('hint_user')) ?></p>
      </div>

      <div class="form-actions">
        <button type="submit" name="action" value="save"><?= esc(t('btn_save')) ?></button>
        <button type="submit" name="action" value="reset" class="secondary"
                onclick="return confirm('<?= esc(t('confirm_reset')) ?>')"><?= esc(t('btn_reset')) ?></button>
        <a href="./" class="btn-link"><?= esc(t('btn_back')) ?></a>
      </div>
    </form>
  </div>
</main>
<script>
// Keep lang switcher links also setting the cookie
document.querySelectorAll('a[href^="?lang="]').forEach(a => {
  a.addEventListener('click', function() {
    const l = new URLSearchParams(this.search).get('lang');
    if (l) document.cookie = 'chat_lang=' + l + '; path=/; max-age=' + (365*24*3600);
  });
});
</script>
</body>
</html>
