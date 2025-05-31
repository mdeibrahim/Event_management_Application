/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Templates within theme app (e.g. theme/templates/**/*.html)
    '../templates/**/*.html',
    // Templates in other apps
    '../../**/templates/**/*.html',
    // JavaScript files that might contain Tailwind classes
    '../../**/static/**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
} 