module.exports = {
  apps: [
    {
      name: 'mirae-api',
      script: 'api.py',
      interpreter: 'python3',
      cwd: '/root/mirae-app',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 8000
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/log/mirae/api-error.log',
      out_file: '/var/log/mirae/api-out.log',
      log_file: '/var/log/mirae/api-combined.log',
      time: true
    },
    {
      name: 'mirae-collectors',
      script: 'run_collectors.py',
      interpreter: 'python3',
      cwd: '/root/mirae-app',
      instances: 1,
      autorestart: true,
      watch: false,
      cron_restart: '0 */6 * * *', // 6시간마다 재시작
      env: {
        NODE_ENV: 'production'
      },
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/var/log/mirae/collectors-error.log',
      out_file: '/var/log/mirae/collectors-out.log',
      log_file: '/var/log/mirae/collectors-combined.log',
      time: true
    }
  ]
};