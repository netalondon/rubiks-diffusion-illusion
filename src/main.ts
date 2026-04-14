import './style.css';
import { bootstrapApp } from './app/bootstrap';

const app = document.querySelector<HTMLDivElement>('#app');
if (!app) {
  throw new Error('Missing #app element');
}
const appRoot = app;

bootstrapApp(appRoot).catch((error) => {
  console.error(error);
  appRoot.textContent = 'Failed to load cube face artwork.';
});
