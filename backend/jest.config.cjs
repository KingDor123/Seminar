const { createDefaultPreset } = require("ts-jest");

/** @type {import("jest").Config} **/
module.exports = {
  // Use the ESM preset for ts-jest
  preset: 'ts-jest/presets/default-esm', 
  testEnvironment: "node",
  testPathIgnorePatterns: ["/node_modules/", "/test/"],
  transform: {
    // Override the transform to enable ESM support in ts-jest
    '^.+\.tsx?$': [
      'ts-jest',
      {
        useESM: true,
      },
    ],
  },
  extensionsToTreatAsEsm: ['.ts'],
  moduleNameMapper: {
    // Map .js imports to .ts files for Jest
    '^(\.{1,2}/.*)\.js$': '$1',
  },
};