const jsonStr = {"description": "Chef\\u0027s special"};
try {
    const obj = JSON.parse(jsonStr);
    console.log("Parsed OK:", obj);
} catch (e) {
    console.error("Parse Error:", e);
}
