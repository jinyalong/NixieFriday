<template>
	<view class="content">
		<uni-nav-bar title="登录" statusBar="true" fixed="true" :border="false" background-color="#f5f5f5"></uni-nav-bar>
		<view style="font-size: 36px; margin-top: 100rpx; margin-bottom: 50rpx; font-family:Cambria, Cochin, Georgia, Times, 'Times New Roman', serif ">
			NixieFriday
		</view>
		<view style="width: 80%; display: flex; gap: 15px; flex-direction: column;">
			<uni-easyinput prefixIcon="person-filled" v-model="username" placeholder="请输入用户名" />
			<uni-easyinput prefixIcon="locked-filled" type="password" v-model="password" placeholder="请输入密码"/>
			<button @click="handleConnectMqtt" class="btn-login">登录</button>
		</view>
		
	</view>
</template>

<script>
	import { mapMutations } from 'vuex'

	export default {
		data() {
			return {
				username: 'codefrida',
				password:'853851430'
			}
		},
		onLoad() {
			let userInfo = uni.getStorageSync("userInfo")
			if (userInfo) {
				this.username = userInfo.username || ''
				this.password = userInfo.pwd || ''
			}
		},
		methods: {
			...mapMutations(['setMqttClient']),
			handleConnectMqtt() {
				const host = 'wxs://www.codefriday.cn/mqtt'
				const clientId = 'mqtt_wx_client_' + Math.random().toString(16).substr(2, 8)
				const options = {
				  keepalive: 60,
				  clientId: clientId,
				  clean: true,
				  reconnectPeriod: 1000,
				  connectTimeout: 30 * 1000,
				  username:this.username,
				  password:this.password
				}
				const mqtt = require("../../utils/mqtt.min.js");
				const client = mqtt.connect(host, options)
				const that = this
				client.on('connect', () => {
				  console.log('Client connected:' + clientId)
				  this.setMqttClient(client)
				  uni.navigateTo({
				  	url:'/pages/control/control?username='+that.username
				  })
				  uni.showToast({
				  	icon:'success',
					title:'登录成功'
				  })
				  uni.setStorageSync('userInfo',{'username':this.username, 'pwd':this.password})
				})
				client.on('error', (err) => {
				  console.log('Connection error: ', err)
				  uni.showToast({
				  	icon:'error',
					title:'登录失败'
				  })
				  client.end()
				})
				client.on('reconnect', () => {
				  console.log('Reconnecting...')
				})
				client.on('close', () => {
				  console.log('Closing...')
				})
				
				

			}
		}
	}
</script>

<style>
.content {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
}

.logo {
	height: 100rpx;
	width: 200rpx;
	margin-top: 200rpx;
	margin-left: auto;
	margin-right: auto;
	margin-bottom: 50rpx;
}
.btn-login{
	margin-top: 15px;
	width: 70%;
	border-radius: 14px;
	background-image: linear-gradient(135deg, #43CBFF 10%, #9708CC 100%);
	color: white;
	font-size: 18px;
	letter-spacing: 1.5px;
}
</style>
