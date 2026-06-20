const { execSync } = require('child_process');
const path = require('path');

const BASE_URL = 'http://localhost:8001';
const API_KEY = 'dev-key-change-me';

// Paths relative to repo root
const PROJECTS = {
  'research-agent': {
    envFile: path.resolve(__dirname, '../upwork-project/research-agent/.env'),
    screenshotDir: (provider) => path.resolve(__dirname, `../screenshots/${provider}`),
  },
};

const PROVIDERS = {
  openai: {
    LLM_PROVIDER: 'openai',
    LOCAL_BASE_URL: '',
    LOCAL_MODEL: '',
    LOCAL_API_KEY: '',
  },
  local: {
    LLM_PROVIDER: 'local',
    LOCAL_BASE_URL: 'http://host.docker.internal:8085/v1',
    LOCAL_MODEL: 'qwen3',
    LOCAL_API_KEY: 'not-needed',
  },
};

function switchProvider(provider, project = 'research-agent') {
  const cfg = PROVIDERS[provider];
  if (!cfg) throw new Error(`Unknown provider: ${provider}`);

  const fs = require('fs');
  const envFile = PROJECTS[project].envFile;
  let env = fs.readFileSync(envFile, 'utf8');

  env = env.replace(/^LLM_PROVIDER=.*/m, `LLM_PROVIDER=${cfg.LLM_PROVIDER}`);
  env = env.replace(/^LOCAL_BASE_URL=.*/m, `LOCAL_BASE_URL=${cfg.LOCAL_BASE_URL}`);
  env = env.replace(/^LOCAL_MODEL=.*/m, `LOCAL_MODEL=${cfg.LOCAL_MODEL}`);
  env = env.replace(/^LOCAL_API_KEY=.*/m, `LOCAL_API_KEY=${cfg.LOCAL_API_KEY}`);

  fs.writeFileSync(envFile, env);

  execSync(
    'docker rm -f research-agent && docker run -d --name research-agent ' +
    '-p 8001:8000 --add-host=host.docker.internal:host-gateway ' +
    `--env-file ${envFile} research-agent`,
    { stdio: 'pipe' }
  );

  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    try {
      const out = execSync('curl -sf http://localhost:8001/health', { stdio: 'pipe' }).toString();
      if (out.includes('"ok"')) break;
    } catch (_) {}
    execSync('sleep 1');
  }
}

function screenshotDir(provider, project = 'research-agent') {
  return PROJECTS[project].screenshotDir(provider);
}

module.exports = { BASE_URL, API_KEY, switchProvider, screenshotDir };
