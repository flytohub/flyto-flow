/**
 * CE edition adapter.
 * Downstream editions replace this module at build time through
 * FLYTO_UI_EDITION_ENTRY. CE deliberately exports no hosted functionality.
 */
export const routes = []
export const navigationItems = []
export const NavigationExtension = null
export const HeaderActionsExtension = null
export const FooterContentExtension = null
export const AppBanner = null
export const MyTemplatesHeroExtension = null
export const MyTemplatesStatsExtension = null
export const MyTemplatesEmptyExtension = null

export async function installEdition() {}

export function routeGuard() {
  return true
}
