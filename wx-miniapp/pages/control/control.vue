<template>
	<view>
		<uni-nav-bar leftIcon="left" @clickLeft="handleLogout" title="NIXIE-控制面板" statusBar="true" fixed="true" :border="false" background-color="#f5f5f5"></uni-nav-bar>
		<view class="nixie-card">
			<uni-section title="高压开关" type="line">
				<switch style="transform:scale(0.8)" :checked="boostSwitch" @change="handleBoostSwitch" />
			</uni-section>
			<uni-section title="走时模式" type="line">
				<checkbox-group @change="handleTravelTime" style="margin-left: 10px;">
					<label>
						<checkbox value="NORMAL" :checked="travelTimeMode=='NORMAL'"/>普通模式
					</label>
					<label style="margin-left: 20px;">
						<checkbox value="FLOP" :checked="travelTimeMode=='FLOP'"/>翻牌模式
					</label>
				</checkbox-group>
			</uni-section>
			<uni-section title="刷新时间" sub-title="防止阴极中毒" type="line">
				 <uni-data-select
					v-model="flashTime"
					:localdata="flashTimeConfig"
					@change="handleFlashTime"
					:clear="false"
				  ></uni-data-select>
			</uni-section>
			<uni-section title="冒号管" type="line">
				<checkbox-group @change="handleDotMode" style="margin-left: 10px;">
					<label>
						<checkbox value="FLASH" :checked="dotMode=='FLASH'"/>闪烁
					</label>
					<label style="margin-left: 20px;">
						<checkbox value="ON" :checked="dotMode=='ON'"/>常亮
					</label>
					<label style="margin-left: 20px;">
						<checkbox value="OFF" :checked="dotMode=='OFF'"/>关闭
					</label>
				</checkbox-group>
			</uni-section>
			<uni-section title="开机显示" type="line">
				<view style="display: flex; gap: 10px; align-items: center; justify-content: center;">
					<view class="num-box" v-for="(item,index) in startUpDisplay" :key="index">
						{{item}}
					</view>
				</view>
				<button class="btn-setting" @click="inputDialogToggle">设置</button>
			</uni-section>
		</view>
		<!-- 设置开机显示内容弹窗 -->
		<uni-popup ref="inputDialog" type="dialog">
			<uni-popup-dialog ref="inputClose"  mode="input" title="输入开机显示内容" v-model="tempStartUpDisplay"
				placeholder="输入六个数字" @confirm="dialogInputConfirm" @close="dialogInputClose"></uni-popup-dialog>
		</uni-popup>
		<view class="nixie-card">
			<uni-section title="氛围灯" sub-title="可独立控制" type="line">
				<view style="align-items: center; display: flex; flex-direction: column;">
					<view @click="handleChangeColor(mainColor,-1)" 
					style="margin-bottom: 15px; height: 72px; width: 72px; border-radius: 36px;" 
					:style="'background-color:'+mainColor"></view>
					<view style="display: flex; gap: 20px;">
						<view v-for="(item,index) in subColors" :key="index" @click="handleChangeColor(item,index)"
						style="height: 48px; width: 48px; border-radius: 24px;" 
						:style="'background-color:'+item"/>
					</view>
				</view>
			</uni-section>
		</view>
		<view style="display: flex; gap: 10px;">
			<button class="btn-bottom" style="background-image: linear-gradient(135deg, #ff0a37 10%, #cc5991 100%);" @click="handleReset">重置时钟</button>
			<button class="btn-bottom" @click="handleRefresh">刷新状态</button>
		</view>
		<uni-popup ref="colorPickerPopup">
			<view style="padding: 20px 30px; background-color: white; border-radius: 12px;">
				<view style="text-align: center; margin-bottom: 15px; font-weight: 550;">颜色选择</view>
				<zebra-color-picker v-model="editColors"></zebra-color-picker>
				<button class="btn-change-color" @click="confirmChangeColor">确定</button>
			</view>
		</uni-popup>

	</view>
</template>

<script>
	import { mapState } from 'vuex'

	export default {
		computed: {
		    ...mapState(['mqttClient']),
		},
		data() {
			return {
				colorChangeType:-1,
				mainColor:'#000000',
				subColors:['#000000','#000000','#000000','#000000','#000000','#000000'],
				editColors: {
					hex: '#000000'
				},
				startUpDisplay:["0","0","0","0","0","0"],
				flashTimeEnum:{
					5:"SHORT",
					10:"LONG",
					30:"VERYLONG"
				},
				dotEnum:{
					0:"OFF",
					512:"FLASH",
					1023:"ON",
				},
				flashTimeConfig:[
					{"value":5,text:"五分钟（推荐）"},
					{"value":10,text:"十分钟"},
					{"value":30,text:"半小时"}
				],
				boostSwitch:false,
				travelTimeMode:"NORMAL",
				dotMode:"FLASH",
				flashTime:5,
				topic:"",
				username:""
			}
		},
		methods: {
			handleLogout(){
				this.mqttClient.end()
				uni.navigateBack()
				uni.showToast({
					icon:'success',
					title:'已退出登录'
				})
			},
			handleReset(){
				this.sendMessage('RESET')
			},
			handleRefresh(){
				this.sendMessage("UPLOAD_STATUS$1")
			},
			handleChangeColor(color, type){
				this.colorChangeType = type
				this.editColors.hex = color
				this.$refs.colorPickerPopup.open('center')
			},
			hexToRgb(hexStr) {
			  hexStr = hexStr.replace("#", "");
			  // 将十六进制值转换为十进制值
			  var decimal = parseInt(hexStr, 16);
			  var r = (decimal >> 16) & 255; // 获取红分量
			  var g = (decimal >> 8) & 255; // 获取绿分量
			  var b = decimal & 255; // 获取蓝分量
			  return { r, g, b };
			},
			rgbToHex(r, g, b) {
				const hexR = r.toString(16).padStart(2, '0');
				const hexG = g.toString(16).padStart(2, '0');
				const hexB = b.toString(16).padStart(2, '0');
				return `#${hexR}${hexG}${hexB}`;
			},
			confirmChangeColor() {
				let rgbaV = this.hexToRgb(this.editColors.hex)
				let msg = `ws2812$${this.colorChangeType == -1 ? 'ALL': this.colorChangeType}$${rgbaV.r}$${rgbaV.g}$${rgbaV.b}`
				this.sendMessage(msg)
				if (this.colorChangeType == -1) {
					this.mainColor = this.editColors.hex
					for (var i = 0; i < 6; i++) {
						this.subColors[i] = this.editColors.hex
					}
				} else {
					this.subColors[this.colorChangeType] =  this.editColors.hex
				}
				this.$refs.colorPickerPopup.close()
			},
			dialogInputClose(){
				this.$refs.inputClose.val = ''
			},
			dialogInputConfirm(str){
				const pattern = /^\d{6}$/;
				if(pattern.test(str)){
					let msg = `STARTSTR$${str}`
					this.sendMessage(msg)
					uni.showToast({
						icon:'success',
						title:'设置成功'
					})
				} else {
					uni.showToast({
						icon:'error',
						title:'格式错误'
					})
				}
				this.$refs.inputClose.val = ''
			},
			inputDialogToggle() {
				this.$refs.inputDialog.open()
			},
			handleDotMode(e) {
				let temp = e.detail.value
				this.dotMode = temp[temp.length-1]
				let msg = `dot$ALL$${this.dotMode}`
				this.sendMessage(msg)
			},
			handleFlashTime(e) {
				let msg = `FLASHTIME$${this.flashTimeEnum[e]}`
				this.sendMessage(msg)
			},
			handleBoostSwitch(e) {
				this.boostSwitch = e.detail.value
				let msg = `HIGHVOLTAGEBOOST$${this.boostSwitch ? 'ON' : 'OFF'}`
				this.sendMessage(msg)
			},
			handleTravelTime(e){
				let temp = e.detail.value
				this.travelTimeMode = temp[temp.length-1]
				let msg = `hv57708$${this.travelTimeMode}`
				this.sendMessage(msg)
			},
		
			// 状态同步消息处理
			messageHandler(message) {
				let data = JSON.parse(message)
				this.boostSwitch = data['HV_EN'] == 1
				this.travelTimeMode = data['HV57708'] == 1 ? 'FLOP':'NORMAL'
				this.flashTime = data['FLASHTIME']
				this.dotMode = this.dotEnum[data['DOT']]
				this.startUpDisplay = data['STARTSTR'].split("")
				let colorTemp = []
				for (var i = 0; i < 6; i++) {
					let hexColor = this.rgbToHex(data['WS2812'][i][0],data['WS2812'][i][1],data['WS2812'][i][2])
					colorTemp.unshift(hexColor)
				}
				this.subColors = colorTemp
				this.mainColor = colorTemp[0]
				
			},
			sendMessage(msg) {
				console.log(msg)
				this.mqttClient.publish(this.topic, msg, { qos: 0, retain: false })
			}
			
		},
		onLoad(options) {
			this.username = options.username
			this.topic = `${this.username}_sub`
			// Subscribe
			this.mqttClient.subscribe(`${this.username}_pub`, { qos: 0 })
			this.sendMessage('UPLOAD_STATUS$1')
			this.mqttClient.on('message', (topic, message, packet) => {
			  this.messageHandler(message.toString())
			})
			uni.hideKeyboard()
		}
	}
</script>

<style>
.nixie-card {
	margin: 5px 5px;
	border-radius: 12px;
	background-color: white;
	padding: 10px;
	font-size: 18px;
}
.uni-section-content{
	padding-left: 10px !important;
}
.num-box{
	font-size: 18px;
	border-radius: 6px;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 48px;
	width: 48px;
	border: 1px solid #ededed;
}
.btn-setting{
	margin-top: 15px;
	width: 55%;
	border-radius: 14px;
	background-image: linear-gradient(135deg, #43CBFF 10%, #08ccb5 100%);
	color: white;
	font-size: 18px;
	letter-spacing: 3px;
}
.btn-change-color{
	margin-top: 15px;
	width: 80%;
	border-radius: 14px;
	background-image: linear-gradient(135deg, #43CBFF 10%, #08ccb5 100%);
	color: white;
	font-size: 18px;
	letter-spacing: 3px;
}

.btn-bottom{
	margin-top: 15px;
	width: 40%;
	border-radius: 14px;
	background-image: linear-gradient(135deg, #43CBFF 10%, #08ccb5 100%);
	color: white;
	font-size: 18px;
	letter-spacing: 3px;
}

</style>
