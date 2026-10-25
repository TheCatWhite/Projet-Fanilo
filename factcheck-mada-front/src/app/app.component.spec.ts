import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { ComposantApplication } from './app.component';

describe('ComposantApplication', () => {
  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [ComposantApplication],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('crée la coquille de l’application', () => {
    const fixture = TestBed.createComponent(ComposantApplication);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('n’affiche pas la navigation sans authentification', async () => {
    const fixture = TestBed.createComponent(ComposantApplication);
    await fixture.whenStable();
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('app-barre-navigation')).toBeNull();
    expect(element.querySelector('router-outlet')).toBeTruthy();
  });
});
