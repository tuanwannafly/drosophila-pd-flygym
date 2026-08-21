# Developer Guide

- All scripts are defined as ES6 modules. Ensure `type="module"` is used on the `<script>` tag.
- Styling relies exclusively on CSS variables defined in `theme.css`. Do not hardcode colors in JavaScript.
- Maintain a strict decoupling: the Web Platform reads JSON states exported from Python, but does not execute Python code directly.
