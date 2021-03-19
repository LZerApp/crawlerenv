layui.use(['admin', 'jquery', 'convert', 'layer', 'element'], function () {
  let admin = layui.admin;
  let $ = layui.jquery;
  let convert = layui.convert;
  let layelem = layui.element;
  let layer = layui.layer;

  let image = new Image();
  image.src = 'https://i.imgur.com/Ar77xLR.png';
  // image.src = "{{ url_for('static', filename='admin/admin/images/avatar.jpg') }}";
  image.onload = function () {
    $('.layui-nav-img').attr('src', convert.imageToBase64(image));
  };
  // 框架初始化时会读取 根目录下 pear.config.yml 文件作为初始化配置
  // 你可以通过 admin.setConfigPath 方法修改配置文件位置
  // 你可以通过 admin.setConfigType 方法修改配置文件类型
  admin.setConfigType('json');
  admin.setConfigPath(
    "{{ url_for('static', filename='config/pear.config.json') }}"
  );
  admin.render();
  console.log('444');
  layelem.on('nav(layui_nav_right)', function (elem) {
    console.log('6');
    if ($(elem).hasClass('logout')) {
      layer.confirm('確定登出嗎？', function (index) {
        layer.close(index);
        $.ajax({
          url: '/admin/logout',
          type: 'POST',
          dataType: 'json',
          success: function (res) {
            if (res.code == 200) {
              layer.msg(res.msg, {
                icon: 1,
              });
              setTimeout(function () {
                location.href = '/admin';
              }, 333);
            }
          },
        });
      });
    } else if ($(elem).hasClass('password')) {
      layer.open({
        type: 2,
        maxmin: true,
        title: '修改密碼',
        shade: 0.1,
        area: ['300px', '300px'],
        content: MODULE_PATH + '/index/pass',
      });
    } else if ($(elem).hasClass('cache')) {
      $.post(MODULE_PATH + '/index/cache', function (data) {
        layer.msg(data.msg, { time: 1500 });
        location.reload();
      });
    }
  });
});
