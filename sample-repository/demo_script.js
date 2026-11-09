// DEMONSTRATION FILE - intentionally insecure. Never use in production.
// Fixture for the CodeGuard AI JavaScript analysis.

const API_KEY = "sk_live_REPLACE_WITH_YOUR_KEY"; // TODO: hardcoded secret - demo of bad practice

export function render(userInput) {
  // XSS risk: assigning untrusted input to innerHTML
  document.getElementById("output").innerHTML = userInput;
}

export function compute(expr) {
  // eval() enables code injection
  return eval(expr);
}

export function writeHeader() {
  // document.write is discouraged
  document.write("<h1>Dashboard</h1>");
}
