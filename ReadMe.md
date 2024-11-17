

For first-time setup after cloning:
npm install

For development (you need both commands running in separate terminals):
Terminal 1: Watch for React changes
npm run watch

 Terminal 2: Run the Electron app
npm start
For building and packaging the macOS app:
npm run package
Then install the concurrently package:

npm install --save-dev concurrently



Now you can start the entire development environment with just one command:
npm run dev



To kill the app is its running
`ps aux | grep -i Compass | awk '{print $2}' | xargs kill -9`



