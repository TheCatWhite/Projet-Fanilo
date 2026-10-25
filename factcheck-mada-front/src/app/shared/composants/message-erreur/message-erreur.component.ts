import { ChangeDetectionStrategy, Component, Input } from '@angular/core';

export type TypeMessage = 'erreur' | 'avertissement' | 'succes' | 'information';

@Component({
  selector: 'app-message-erreur',
  standalone: true,
  template: `
    @if (messages.length > 0) {
      <div class="message" [class]="'message message--' + type" role="alert">
        <ul>
          @for (message of messages; track $index) {
            <li>{{ message }}</li>
          }
        </ul>
      </div>
    }
  `,
  styleUrl: './message-erreur.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ComposantMessageErreur {
  @Input() messages: string[] = [];
  @Input() type: TypeMessage = 'erreur';
}
