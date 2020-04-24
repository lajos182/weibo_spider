// https://passport.sinaimg.cn/js/sso/ssologin.js
var makeRequest = function (username, password, savestate) {
    var request = {
        entry: me.getEntry(),
        gateway: 1,
        from: me.from,
        savestate: savestate,
        useticket: me.useTicket ? 1 : 0
    };
    if (me.failRedirect) {
        me.loginExtraQuery.frd = 1
    }
    request = objMerge(request, {
        pagerefer: document.referrer || ""
    });
    request = objMerge(request, me.loginExtraFlag);
    request = objMerge(request, me.loginExtraQuery);
    request.su = sinaSSOEncoder.base64.encode(urlencode(username));
    if (me.service) {
        request.service = me.service
    }
    if ((me.loginType & rsa) && me.servertime && sinaSSOEncoder && sinaSSOEncoder.RSAKey) {
        request.servertime = me.servertime;
        request.nonce = me.nonce;
        request.pwencode = "rsa2";
        request.rsakv = me.rsakv;
        var RSAKey = new sinaSSOEncoder.RSAKey();
        RSAKey.setPublic(me.rsaPubkey, "10001");
        password = RSAKey.encrypt([me.servertime, me.nonce].join("\t") + "\n" + password)
    } else {
        if ((me.loginType & wsse) && me.servertime && sinaSSOEncoder && sinaSSOEncoder.hex_sha1) {
            request.servertime = me.servertime;
            request.nonce = me.nonce;
            request.pwencode = "wsse";
            password = sinaSSOEncoder.hex_sha1("" + sinaSSOEncoder.hex_sha1(sinaSSOEncoder.hex_sha1(password)) + me.servertime + me.nonce)
        }
    }
    request.sp = password;
    try {
        request.sr = window.screen.width + "*" + window.screen.height
    } catch (e) {
    }
    return request
};