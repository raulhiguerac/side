const { defineConfig } = require("@vue/cli-service");
const webpack = require("webpack");

// module.exports = defineConfig({
//   transpileDependencies: true,
// });

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    proxy: {
      "/api/users": {
        target: "http://localhost:8000",
        changeOrigin: true,
        pathRewrite: { "^/api/users": "" },
      },
      "/api/catalog": {
        target: "http://localhost:8001",
        changeOrigin: true,
        pathRewrite: { "^/api/catalog": "" },
      },
      "/api/avm": {
        target: "http://localhost:8002",
        changeOrigin: true,
        pathRewrite: { "^/api/avm": "" },
      },
      "/api/properties": {
        target: "http://localhost:8003",
        changeOrigin: true,
        pathRewrite: { "^/api/properties": "" },
      },
    },
  },
  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        // Vue CLI is in maintenance mode, and probably won't merge my PR to fix this in their tooling
        // https://github.com/vuejs/vue-cli/pull/7443
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: "false",
      }),
    ],
    watchOptions: {
      poll: 1000,
      ignored: /node_modules/,
    },
  },
});
