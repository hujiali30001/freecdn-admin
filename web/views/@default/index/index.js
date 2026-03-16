// FreeCDN: 替换登录页面中的 GoEdge 品牌字样
;(function patchLoginBrand() {
	function replaceTextNodes(node) {
		if (node.nodeType === 3) {
			node.textContent = node.textContent.replace(/GoEdge/g, 'FreeCDN')
		} else if (node.childNodes) {
			node.childNodes.forEach(replaceTextNodes)
		}
	}
	document.addEventListener('DOMContentLoaded', function() {
		document.title = document.title.replace(/GoEdge/g, 'FreeCDN')
		var header = document.querySelector('.ui.header')
		if (header) replaceTextNodes(header)
	})
})();

/**
 * 校验重定向目标是否为同域，防止开放重定向攻击
 * @param {string} url
 * @returns {boolean}
 */
function isSameOriginURL(url) {
	if (!url || url.length === 0) {
		return false
	}
	// 允许相对路径（以 / 开头但不以 // 开头）
	if (/^\/[^/]/.test(url) || url === '/') {
		return true
	}
	try {
		var parsed = new URL(url, window.location.origin)
		return parsed.origin === window.location.origin
	} catch (e) {
		return false
	}
}

Tea.context(function () {
	this.username = ""
	this.password = ""
	this.passwordMd5 = ""
	this.encodedFrom = window.encodeURIComponent(this.from)

	// RED-08: 移除 Demo 模式硬编码明文密码
	// 如需演示账号，请通过 create-admin 工具单独创建演示账号

	this.isSubmitting = false

	this.$delay(function () {
		this.$find("form input[name='username']").focus()
		this.changePassword()
	});

	this.changeUsername = function () {

	}

	this.changePassword = function () {
		this.passwordMd5 = md5(this.password.trim());
	};

	// 更多选项
	this.moreOptionsVisible = false;
	this.showMoreOptions = function () {
		this.moreOptionsVisible = !this.moreOptionsVisible;
	};

	this.submitBefore = function () {
		this.isSubmitting = true;
	};

	this.submitDone = function () {
		this.isSubmitting = false;
	};

	this.submitSuccess = function (resp) {
		// ORA-06: localSid/ip 仅作为辅助显示用途存入 localStorage
		// 真正的鉴权依赖后端 HttpOnly Cookie（sid），前端无法访问
		if (resp.data.localSid) {
			localStorage.setItem("sid", resp.data.localSid)
		}
		if (resp.data.ip) {
			localStorage.setItem("ip", resp.data.ip)
		}

		// redirect back
		this.$delay(function () {
			if (resp.data.requireOTP) {
				window.location = "/index/otp?sid=" + resp.data.sid + "&remember=" + (resp.data.remember ? 1 : 0) + "&from=" + window.encodeURIComponent(this.from)
				return
			}
			// ORA-07: 开放重定向校验，确保只跳转到同域地址
			if (this.from.length > 0 && isSameOriginURL(this.from)) {
				window.location = this.from;
			} else {
				window.location = "/dashboard";
			}
		})
	};
});
