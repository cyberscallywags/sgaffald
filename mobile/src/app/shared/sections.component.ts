import { Component, input } from '@angular/core';
import {
  IonBadge,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonText,
} from '@ionic/angular';

import { Section } from '../core/api.service';
import { iconName } from '../core/icons';

/** Renders manifest sections; the mobile twin of render_section in app/ui/main.py. */
@Component({
  selector: 'app-sections',
  templateUrl: 'sections.component.html',
  styleUrls: ['sections.component.scss'],
  imports: [
    IonBadge,
    IonCard,
    IonCardContent,
    IonCardHeader,
    IonCardTitle,
    IonIcon,
    IonItem,
    IonLabel,
    IonList,
    IonText,
  ],
})
export class SectionsComponent {
  readonly sections = input.required<Section[]>();
  protected readonly iconName = iconName;
}
