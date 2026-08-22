const window = { socket: null, location: { protocol: 'https:' } };
const document = { 
    querySelector: () => ({ style: {}, classList: { add: () => {}, remove: () => {} }, innerHTML: '', appendChild: () => {}, display: '' }),
    querySelectorAll: () => [],
    getElementById: () => ({ style: {}, classList: { add: () => {}, remove: () => {} }, innerHTML: '', appendChild: () => {}, display: '', innerText: '' }),
    createElement: () => ({ classList: { add: () => {} }, setAttribute: () => {} })
};
const io = () => ({ on: () => {} });
const localStorage = { getItem: () => null, setItem: () => {} };
const fetch = async () => {};
const alert = () => {};
const console = { log: () => {}, error: () => {} };
const navigator = { serviceWorker: { register: async () => {} } };

try {
    // Paste the JS here
    eval(require('fs').readFileSync('live_orders.js', 'utf8'));
    console.log("No runtime errors on initialization!");
} catch (e) {
    console.error("RUNTIME ERROR:", e);
}
