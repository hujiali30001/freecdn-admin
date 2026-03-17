#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const less = require('less');

const baseDir = 'c:\\Users\\Administrator\\.workbuddy\\FreeCDN\\web\\views\\@default';

const filesToCompile = [
    { input: '@design_tokens.less', output: '@design_tokens.css' },
    { input: '@components_base.less', output: '@components_base.css' },
    { input: '@components_data.less', output: '@components_data.css' },
    { input: '@components_feedback.less', output: '@components_feedback.css' },
    { input: '@globals_utilities.less', output: '@globals_utilities.css' },
    { input: 'dashboard/index.less', output: 'dashboard/index.css' },
    { input: 'clusters/index.less', output: 'clusters/index.css' },
    { input: 'servers/index.less', output: 'servers/index.css' },
    { input: 'users/features.less', output: 'users/features.css' },
    { input: 'nodes/index.less', output: 'nodes/index.css' },
    { input: 'admins/index.less', output: 'admins/index.css' },
    { input: 'settings/index.less', output: 'settings/index.css' },
    { input: 'dns/index.less', output: 'dns/index.css' },
    { input: 'index/index.less', output: 'index/index.css' },
    { input: 'log/index.less', output: 'log/index.css' },
    { input: 'setup/index.less', output: 'setup/index.css' },
    { input: 'db/index.less', output: 'db/index.css' },
    { input: 'ui/index.less', output: 'ui/index.css' },
];


console.log('='.repeat(60));
console.log('LESS 编译脚本（Node.js）');
console.log('='.repeat(60));

async function compile(inputFile, outputFile) {
    const inputPath = path.join(baseDir, inputFile);
    const outputPath = path.join(baseDir, outputFile);
    
    try {
        const lessCode = fs.readFileSync(inputPath, 'utf8');
        
        console.log(`\n编译 ${inputFile}...`);
        
        const result = await less.render(lessCode, {
            filename: inputPath,
            paths: [baseDir]
        });
        
        fs.writeFileSync(outputPath, result.css, 'utf8');
        console.log(`✓ 编译成功: ${outputFile}`);
        return true;
    } catch (error) {
        console.log(`✗ 编译失败: ${inputFile}`);
        console.log(`  错误: ${error.message}`);
        return false;
    }
}

async function compileAll() {
    let success = 0;
    let fail = 0;
    
    for (const file of filesToCompile) {
        const result = await compile(file.input, file.output);
        if (result) success++;
        else fail++;
    }
    
    console.log('\n' + '='.repeat(60));
    console.log(`编译完成: ${success} 成功, ${fail} 失败`);
    console.log('='.repeat(60));
}

compileAll().catch(console.error);
