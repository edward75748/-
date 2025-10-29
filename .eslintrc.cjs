module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: ['eslint:recommended', 'plugin:import/recommended', 'prettier'],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  settings: {
    'import/resolver': {
      node: {
        extensions: ['.js', '.ts']
      }
    }
  },
  rules: {
    'import/extensions': 'off',
    'no-console': ['warn', { allow: ['warn', 'error'] }]
  },
  overrides: [
    {
      files: ['tests/**/*.spec.ts'],
      env: {
        node: true
      }
    }
  ]
};
