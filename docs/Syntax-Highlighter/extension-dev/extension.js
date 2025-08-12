const vscode = require("vscode");

function activate(context) {
  console.log("CTX-CARD syntax highlighting extension is now active!");

  // Register a simple command to test activation
  let disposable = vscode.commands.registerCommand(
    "ctx-card-syntax.helloWorld",
    () => {
      vscode.window.showInformationMessage(
        "CTX-CARD syntax highlighting is working!"
      );
    }
  );

  context.subscriptions.push(disposable);
}

function deactivate() {
  console.log("CTX-CARD syntax highlighting extension is now deactivated!");
}

module.exports = {
  activate,
  deactivate,
};
