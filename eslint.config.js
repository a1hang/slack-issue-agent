// ESLint flat config for project root
export default [
  {
    files: ["cdk/**/*.ts"],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
    },
    rules: {},
  },
  {
    ignores: [
      "**/node_modules/**",
      "**/cdk.out/**",
      "**/*.js",
      "**/*.d.ts",
      ".devcontainer/**",
    ],
  },
];
