import adapter from '@sveltejs/adapter-auto';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter()
	},
	compilerOptions: {
		warningFilter: (warning) => !warning.code.startsWith('a11y')
	}
};

export default config;
