const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:3001',
      changeOrigin: true,
      secure: false,
      logLevel: 'warn',
      pathRewrite: (path, req) => {
        return path.replace(/^\/api/, '/api/v1');
      }
    })
  );
};
