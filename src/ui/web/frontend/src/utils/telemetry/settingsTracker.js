/**
 * Settings Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks settings events only.
 */

import { telemetry } from '@/services/telemetry'
import { SETTINGS_EVENTS } from '@/constants/telemetryEvents'

export const trackSettings = {
  change: (settingName, oldValue, newValue) => {
    telemetry.track(SETTINGS_EVENTS.CHANGE, {
      setting_name: settingName,
      old_value: oldValue,
      new_value: newValue,
    })
  },

  themeSwitch: (theme) => {
    telemetry.track(SETTINGS_EVENTS.THEME_SWITCH, { theme })
  },

  languageChange: (oldLang, newLang) => {
    telemetry.track(SETTINGS_EVENTS.LANGUAGE_CHANGE, { old_lang: oldLang, new_lang: newLang })
  },
}
