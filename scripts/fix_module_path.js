#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const OLD = 'github.com/TeaOSLab/EdgeAdmin';
const NEW = 'github.com/hujiali30001/freecdn-admin';
const ROOT = path.resolve(__dirname, '..');

let changedFiles = 0, totalReplacements = 0;

function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    if (name === '.git' || name === 'dist' || name === 'build') continue;
    const full = path.join(dir, name);
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      walk(full);
    } else if (name.endsWith('.go')) {
      const content = fs.readFileSync(full, 'utf8');
      if (content.includes(OLD)) {
        const count = (content.match(new RegExp(OLD.replace(/\//g, '\\/'), 'g')) || []).length;
        const newContent = content.split(OLD).join(NEW);
        fs.writeFileSync(full, newContent, 'utf8');
        changedFiles++;
        totalReplacements += count;
        console.log(`  fixed: ${path.relative(ROOT, full)} (${count}x)`);
      }
    }
  }
}

walk(ROOT);
console.log(`\nDone: ${changedFiles} files changed, ${totalReplacements} replacements total`);
