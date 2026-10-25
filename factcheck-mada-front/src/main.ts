import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { ComposantApplication } from './app/app.component';

bootstrapApplication(ComposantApplication, appConfig).catch((err) => console.error(err));
