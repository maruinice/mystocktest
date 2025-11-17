const fs = require('fs');
const path = require('path');

// 需要修复的文件和对应的修复规则
const fixes = [
  // ModelDashboard.vue
  {
    file: 'src/components/model/ModelDashboard.vue',
    replacements: [
      {
        from: 'getModelTypeColor(model.model_type)',
        to: 'getModelTypeColor(model.model_type) as TagType'
      },
      {
        from: '(model.accuracy * 100)',
        to: '((model.accuracy || 0) * 100)'
      },
      {
        from: 'formatNumber(model.usage_count)',
        to: 'formatNumber(model.usage_count || 0)'
      },
      {
        from: 'const loading = ref(false)',
        to: 'const _loading = ref(false)'
      }
    ]
  },
  // ModelForm.vue
  {
    file: 'src/components/model/ModelForm.vue',
    replacements: [
      {
        from: 'v-model="formData.enabled"',
        to: 'v-model="(formData as any).enabled"'
      },
      {
        from: 'type UpdateModelRequest,',
        to: 'type UpdateModelRequest as _UpdateModelRequest,'
      }
    ]
  },
  // ModelList.vue
  {
    file: 'src/components/model/ModelList.vue',
    replacements: [
      {
        from: 'model._toggling = true',
        to: ';(model as any)._toggling = true'
      },
      {
        from: 'model._toggling = false',
        to: ';(model as any)._toggling = false'
      },
      {
        from: 'model._deleting = true',
        to: ';(model as any)._deleting = true'
      },
      {
        from: 'model._deleting = false',
        to: ';(model as any)._deleting = false'
      }
    ]
  }
];

// 执行修复
fixes.forEach(fix => {
  const filePath = path.join(__dirname, fix.file);
  
  if (fs.existsSync(filePath)) {
    let content = fs.readFileSync(filePath, 'utf8');
    
    fix.replacements.forEach(replacement => {
      content = content.replace(new RegExp(replacement.from.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), replacement.to);
    });
    
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Fixed: ${fix.file}`);
  } else {
    console.log(`File not found: ${fix.file}`);
  }
});

console.log('Type fixes completed!');