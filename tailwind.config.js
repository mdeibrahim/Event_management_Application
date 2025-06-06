/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './core/templates/**/*.html',
      './templates/**/*.html',
      './users/templates/**/*.html',
      './**/templates/**/*.html',
      './static/**/*.js',
    ],
    theme: {
      extend: {
        colors: {
          'primary': '#4f46e5',
          'secondary': '#7c3aed',
        },
        animation: {
          'fade-in-up': 'fade-in-up 0.6s ease-out forwards',
          'fade-in': 'fade-in 0.6s ease-out forwards',
        },
        keyframes: {
          'fade-in-up': {
            '0%': {
              opacity: '0',
              transform: 'translateY(20px)'
            },
            '100%': {
              opacity: '1',
              transform: 'translateY(0)'
            },
          },
          'fade-in': {
            '0%': {
              opacity: '0'
            },
            '100%': {
              opacity: '1'
            },
          }
        }
      },
    },
    plugins: [],
  };
  