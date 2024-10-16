module.exports = {
    content: [
        'app/**/*.html',
        'assets/**/*.ts',
        'node_modules/preline/dist/*.js',
    ],
    plugins: [
        require('preline/plugin'),
    ]
};
