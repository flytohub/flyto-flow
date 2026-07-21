/**
 * Project Store - Phase 7 Multi-tenancy
 * Manages project CRUD and membership
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsAPI } from '@/api/projects'
import i18n from '@/i18n'
import { asObject, asRecordArray } from '@/utils/dataBoundary'

export const useProjectStore = defineStore('projects', () => {
  // ========== State ==========
  const projects = ref([])
  const currentProject = ref(null)
  const projectMembers = ref([])
  const isLoading = ref(false)
  const isLoadingMembers = ref(false)
  const error = ref(null)

  // ========== Getters ==========
  const hasProjects = computed(() => projects.value.length > 0)
  const projectCount = computed(() => projects.value.length)

  // ========== Actions ==========

  /**
   * Fetch all projects
   * @returns {Promise<Object>}
   */
  async function fetchProjects() {
    isLoading.value = true
    error.value = null

    try {
      const result = await projectsAPI.getProjects()
      const normalized = asObject(result)
      if (normalized.ok) {
        projects.value = asRecordArray(normalized.projects)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchProjects')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch single project
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async function fetchProject(projectId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await projectsAPI.getProject(projectId)
      const normalized = asObject(result)
      if (normalized.ok) {
        currentProject.value = Object.keys(asObject(normalized.project)).length > 0 ? asObject(normalized.project) : null
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchProject')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create new project
   * @param {Object} data - Project data
   * @returns {Promise<Object>}
   */
  async function createProject(data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await projectsAPI.create(data)
      const normalized = asObject(result)
      const project = asObject(normalized.project)
      if (normalized.ok && Object.keys(project).length > 0) {
        projects.value.push(project)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToCreateProject')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update project
   * @param {string} projectId - Project ID
   * @param {Object} data - Update data
   * @returns {Promise<Object>}
   */
  async function updateProject(projectId, data) {
    isLoading.value = true
    error.value = null

    try {
      const result = await projectsAPI.update(projectId, data)
      const normalized = asObject(result)
      if (normalized.ok) {
        const index = projects.value.findIndex(p => p?.id === projectId)
        if (index !== -1) {
          projects.value[index] = { ...projects.value[index], ...data }
        }
        if (currentProject.value?.id === projectId) {
          currentProject.value = { ...currentProject.value, ...data }
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToUpdateProject')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Delete project
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async function deleteProject(projectId) {
    isLoading.value = true
    error.value = null

    try {
      const result = await projectsAPI.delete(projectId)
      const normalized = asObject(result)
      if (normalized.ok) {
        projects.value = projects.value.filter(p => p?.id !== projectId)
        if (currentProject.value?.id === projectId) {
          currentProject.value = null
        }
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToDeleteProject')
      return { ok: false, error: error.value }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch project members
   * @param {string} projectId - Project ID
   * @returns {Promise<Object>}
   */
  async function fetchProjectMembers(projectId) {
    isLoadingMembers.value = true
    error.value = null

    try {
      const result = await projectsAPI.getMembers(projectId)
      const normalized = asObject(result)
      if (normalized.ok) {
        projectMembers.value = asRecordArray(normalized.members)
      } else {
        error.value = normalized.error
      }
      return result
    } catch (err) {
      error.value = err.message || i18n.global.t('error.failedToFetchMembers')
      return { ok: false, error: error.value }
    } finally {
      isLoadingMembers.value = false
    }
  }

  /**
   * Clear current project
   */
  function clearCurrentProject() {
    currentProject.value = null
    projectMembers.value = []
  }

  /**
   * Clear error
   */
  function clearError() {
    error.value = null
  }

  /**
   * Reset state
   */
  function reset() {
    projects.value = []
    currentProject.value = null
    projectMembers.value = []
    isLoading.value = false
    isLoadingMembers.value = false
    error.value = null
  }

  return {
    // State
    projects,
    currentProject,
    projectMembers,
    isLoading,
    isLoadingMembers,
    error,

    // Getters
    hasProjects,
    projectCount,

    // Actions
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject,
    fetchProjectMembers,
    clearCurrentProject,
    clearError,
    reset
  }
})
