/**
 * HTTP Body State Management
 *
 * Manages body type switching (none/json/form/raw) and
 * body content state for HTTP node params.
 */
import { ref } from 'vue'

export function useHttpBody(localParams, emitUpdate) {
  const bodyType = ref('none')
  const bodyJsonString = ref('{}')
  const formDataObj = ref({})

  function initBody() {
    if (!localParams.value.body) {
      bodyType.value = 'none'
    } else if (typeof localParams.value.body === 'object') {
      if (localParams.value.contentType?.includes('form')) {
        bodyType.value = 'form'
        formDataObj.value = { ...localParams.value.body }
      } else {
        bodyType.value = 'json'
        bodyJsonString.value = JSON.stringify(localParams.value.body, null, 2)
      }
    } else {
      bodyType.value = 'raw'
    }
  }

  function setBodyType(type) {
    bodyType.value = type

    if (type === 'none') {
      localParams.value.body = null
      localParams.value.contentType = 'application/json'
    } else if (type === 'json') {
      localParams.value.contentType = 'application/json'
      try {
        localParams.value.body = JSON.parse(bodyJsonString.value)
      } catch {
        localParams.value.body = {}
      }
    } else if (type === 'form') {
      localParams.value.contentType = 'application/x-www-form-urlencoded'
      localParams.value.body = { ...formDataObj.value }
    } else if (type === 'raw') {
      localParams.value.contentType = 'text/plain'
      localParams.value.body = ''
    }

    emitUpdate()
  }

  function onBodyJsonChange(value) {
    bodyJsonString.value = value
    try {
      localParams.value.body = JSON.parse(value)
    } catch {
      localParams.value.body = value
    }
    emitUpdate()
  }

  function onFormDataChange(value) {
    formDataObj.value = value
    localParams.value.body = value
    emitUpdate()
  }

  return {
    bodyType,
    bodyJsonString,
    formDataObj,
    initBody,
    setBodyType,
    onBodyJsonChange,
    onFormDataChange
  }
}
