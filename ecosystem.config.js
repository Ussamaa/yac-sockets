module.exports = {
  apps: [{
    name: 'market-server',
    script: '/usr/bin/python3.11',
    args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8001',
    cwd: '/root/market-server',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/pm2-error.log',
    out_file: './logs/pm2-out.log',
    log_file: './logs/pm2-combined.log',
    time: true
  }]
};
