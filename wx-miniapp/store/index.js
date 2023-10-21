import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    mqttClient: null
  },
  mutations: {
    setMqttClient(state, client) {
      state.mqttClient = client
    }
  }
})

export default store
