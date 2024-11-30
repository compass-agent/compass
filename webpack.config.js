const path = require("path");
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: "development",
  entry: "./frontend/renderer/index.js",
  output: {
    path: path.resolve(__dirname, "frontend/renderer/build"),
    filename: "renderer.js",
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
              [
                "@babel/preset-react",
                {
                  runtime: "automatic",
                },
              ],
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.scss$/,
        use: [
          "style-loader", // Injects styles into DOM
          "css-loader", // Turns CSS into CommonJS
          "sass-loader", // Compiles Sass to CSS
        ],
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js", ".jsx"],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: path.join(__dirname, 'frontend/renderer/index.html'), // Use the `index.html` from `renderer`
      filename: 'index.html', // Output it to the `build` directory
    }),
  ],
  devServer: {
    static: path.join(__dirname, 'frontend/renderer/build'),
    compress: true,
    port: 9000,
    hot: true,
    historyApiFallback: true, // This serves index.html for all routes // React SPA support
  },
  devtool: "source-map",
};
