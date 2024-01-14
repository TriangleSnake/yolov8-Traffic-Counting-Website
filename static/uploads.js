document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();

    var formData = new FormData();
    var fileInput = document.getElementById('fileInput');
    var progressBar = document.getElementById('progressBar');

    formData.append('file', fileInput.files[0]);

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true); // 你的后端文件上传接口

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            var percentComplete = (e.loaded / e.total) * 100;
            progressBar.style.width = percentComplete + '%';
            progressBar.textContent = Math.round(percentComplete) + '%';
        }
    };

    xhr.onload = function() {
        if (xhr.status === 200) {
            document.location.href = '/draw'
            alert('上傳成功');
        } else {
            alert('上傳失敗');
        }
    };

    xhr.send(formData);
});