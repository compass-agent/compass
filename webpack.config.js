const path = require("path");

module.exports = {
  mode: "development",
  entry: {
    app: './frontend/renderer/index.js',
    templateTraining: './frontend/renderer/template-training/index.js'
  },
  output: {
    path: path.resolve(__dirname, "frontend/renderer/dist"),
    filename: "[name].bundle.js",
    clean: true,
    publicPath: '/',
  },
  cache: false,
  optimization: {
    moduleIds: 'deterministic',
    removeAvailableModules: false,
    removeEmptyChunks: false,
    splitChunks: false,
  },
  watchOptions: {
    ignored: /node_modules/,
    poll: 1000,
    aggregateTimeout: 300,
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        exclude: /node_modules/,
        use: 'ts-loader',
      },
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: [
              "@babel/preset-env",
              ["@babel/preset-react", { runtime: "automatic" }],
            ],
            cacheDirectory: false,
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.scss$/,
        use: ["style-loader", "css-loader", "sass-loader"],
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js", ".jsx"],
  },
  devtool: "source-map",
};
