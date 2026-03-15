const fs = require('fs');
const path = require('path');
const ROOT = 'C:\\Users\\Administrator\\.workbuddy\\FreeCDN';
let found = [];
function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    if (['.git','dist','build'].includes(name)) continue;
    const full = path.join(dir, name);
    if (fs.statSync(full).isDirectory()) walk(full);
    else if (name.endsWith('.go')) {
      const c = fs.readFileSync(full,'utf8');
      if (c.includes('EdgePlus')) found.push(path.relative(ROOT, full));
    }
  }
}
walk(ROOT);
console.log(found.length ? found.join('\n') : 'No EdgePlus references found in .go files');
