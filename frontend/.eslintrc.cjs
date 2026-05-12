module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    es2022: true,
    jest: true,
  },
  extends: [
    "next/core-web-vitals",
    "next/typescript",
    "plugin:jest/recommended",
  ],
  plugins: ["jest"],
  rules: {
    "@typescript-eslint/no-explicit-any": "off",
    "@typescript-eslint/no-unused-vars": [
      "warn",
      {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      },
    ],
    "react/no-unescaped-entities": "off",
    "@next/next/no-html-link-for-pages": "off",
    "prefer-const": "warn",
  },
  ignorePatterns: [".next/", "node_modules/", "public/", "artifacts/"],
  overrides: [
    {
      files: [
        "__tests__/**/*.ts",
        "__tests__/**/*.tsx",
        "tests/**/*.ts",
        "tests/**/*.tsx",
      ],
      env: {
        jest: true,
      },
    },
  ],
};
