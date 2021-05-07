function getImage() {

    var canvas = document.getElementById('canvas'),
        context = canvas.getContext('2d');

    var base_image = new Image();

    base_image.src = document.getElementById('imagename').value; //Load Image ;
    base_image.onload = function () {
        context.drawImage(base_image, 0, 0);
    }
    canvas.width = base_image.width;
    canvas.height = base_image.height;

    function drawImage() {
    }
    var strokeWidth = 3;
    drawCount = 0;

    canvas.addEventListener("mousemove", function (e) {
        drawRectangleOnCanvas.handleMouseMove(e);
    }, false);
    canvas.addEventListener("mousedown", function (e) {
        drawRectangleOnCanvas.handleMouseDown(e);
    }, false);
    canvas.addEventListener("mouseup", function (e) {
        drawRectangleOnCanvas.handleMouseUp(e);
    }, false);
    canvas.addEventListener("mouseout", function (e) {
        drawRectangleOnCanvas.handleMouseOut(e);
    }, false);

    function reOffset() {
        var BB = canvas.getBoundingClientRect();
        recOffsetX = BB.left;
        recOffsetY = BB.top;
    }

    var recOffsetX, recOffsetY;
    reOffset();

    window.onscroll = function (e) {
        reOffset();
    }
    window.onresize = function (e) {
        reOffset();
    }

    var isRecDown = false;
    var startX, startY;

    var rects = [];
    var newRect;

    var jsonTemplate = {};

    var test_json_push = {};
    var descriptionValue = document.getElementById('descriptionValue').value; //Load Image ;
    jsonTemplate["description"] = descriptionValue;
    var docsValue = document.getElementById('docsValue').value; //Load Image ;
    jsonTemplate["docs"] = docsValue;
    jsonTemplate["image_url"] = base_image.src;
    jsonTemplate["layout"] = (document.getElementById('templateNameValue').value + "_layout");

    jsonTemplate["usage"] = 0;
    jsonTemplate["textboxes"] = [];
    jsonTemplate["name"] = document.getElementById('templateNameValue').value;

    var drawRectangleOnCanvas = {

        handleMouseDown: function (e) {
            
            // tell the browser we're handling this event
            e.preventDefault();
            e.stopPropagation();

            startX = parseInt(e.clientX - recOffsetX);
            startY = parseInt(e.clientY - recOffsetY);

            //jsonTemplate.textboxes[drawCount]['left'] = (startX / base_image.width).toFixed(3);
            //jsonTemplate.textboxes[drawCount]['up'] = (startY / base_image.height).toFixed(3);

            test_json_push = {
                "left": (startX / base_image.width).toFixed(3),
                "top": (startY / base_image.height).toFixed(3)
            }

            jsonTemplate.textboxes.push(test_json_push);

            // Put your mousedown stuff here
            isRecDown = true;

        },

        handleMouseUp: function (e) {

            // tell the browser we're handling this event
            e.preventDefault();
            e.stopPropagation();

            mouseX = parseInt(e.clientX - recOffsetX);
            mouseY = parseInt(e.clientY - recOffsetY);

            // Put your mouseup stuff here
            isRecDown = false;

            //test_json_push = test_json_push + {
            //"right": (mouseX / base_image.width).toFixed(3),
            //"down": (mouseY / base_image.height).toFixed(3)
            //}
            //jsonTemplate.textboxes.push(test_json_push);
            jsonTemplate.textboxes[drawCount]['right'] = (mouseX / base_image.width).toFixed(3);
            jsonTemplate.textboxes[drawCount]['bottom'] = (mouseY / base_image.height).toFixed(3);



            //console.log(JSON.stringify(jsonTemplate, null, 2));
            //console.log(drawCount);
            drawCount = drawCount + 1;


            // Create new form fields dynamically when every 
            var form = document.createElement("form");
            form.setAttribute("method", "post");

            // Create an input element for color
            var colorCount = "color" + drawCount;
            var color = document.createElement("input");
            color.setAttribute("type", "text");
            color.setAttribute("id", colorCount);
            color.setAttribute("docId", drawCount);
            color.setAttribute("placeholder", colorCount);
            // Append the color input to the form 
            form.appendChild(color);


            // Create an input element for font
            var fontCount = "font" + drawCount;
            var font = document.createElement("input");
            font.setAttribute("type", "text");
            font.setAttribute("id", fontCount);
            font.setAttribute("docId", drawCount);
            font.setAttribute("placeholder", fontCount);
            // Append the font input to the form 
            form.appendChild(font);

            // Create an input element for justify
            var justifyCount = "justify" + drawCount;
            var justify = document.createElement("input");
            justify.setAttribute("type", "text");
            justify.setAttribute("id", justifyCount);
            justify.setAttribute("docId", drawCount);
            justify.setAttribute("placeholder", justifyCount);
            // Append the justify input to the form 
            form.appendChild(justify);

            // Create an concat element for justify
            var concatCount = "concat" + drawCount;
            var concat = document.createElement("input");
            concat.setAttribute("type", "text");
            concat.setAttribute("id", concatCount);
            concat.setAttribute("docId", drawCount);
            concat.setAttribute("placeholder", concatCount);
            // Append the concat input to the form 
            form.appendChild(concat);

            // Create an outline element for justify
            var outlineCount = "outline" + drawCount;
            var outline = document.createElement("input");
            outline.setAttribute("type", "text");
            outline.setAttribute("id", outlineCount);
            outline.setAttribute("docId", drawCount);
            outline.setAttribute("placeholder", outlineCount);
            // Append the outline input to the form 
            form.appendChild(outline);


            if (drawCount == 1) {
                // create a submit button 
                var s = document.createElement("input");
                s.setAttribute("type", "button");
                s.setAttribute("id", "submitButton");
                s.setAttribute("value", "submit");

                // Append the submit button to the form 
                form.appendChild(s);
            }

            document.getElementsByTagName("body")[0]
                .appendChild(form);



            //if(!willOverlap(newRect)){
            rects.push(newRect);
            //}
            drawRectangleOnCanvas.drawAll()

        },

        drawAll: function () {
            context.clearRect(0, 0, canvas.width, canvas.height);
            context.drawImage(base_image, 0, 0);
            context.lineWidth = strokeWidth;
            for (var i = 0; i < rects.length; i++) {
                var r = rects[i];
                context.strokeStyle = r.color;
                context.globalAlpha = 1;
                context.strokeRect(r.left, r.top, r.right - r.left, r.bottom - r.top);

                context.beginPath();
                //context.arc(r.left, r.top, 15, 0, Math.PI * 2, true);
                context.closePath();
                context.fillStyle = r.color;
                context.fill();

                var text = drawCount;
                context.fillStyle = "#fff";
                var font = "bold " + 2 + "px serif";
                context.font = font;
                var width = context.measureText(text).width;
                var height = context.measureText("w").width; // this is a GUESS of height
                context.fillText(text, r.left - (width / 2), r.top + (height / 2));


                // submit support after
                if (drawCount != 0) {
                    document.getElementById('submitButton').onclick = function () {
                        var numberOfTextboxes = drawCount;
                        jsonTemplate.textboxes.forEach(addData)
                        function addData(item, index) {
                            var colorIndex = `color${index}`;
                            jsonTemplate.textboxes[index]['color'] = document.getElementById(("color" + (index + 1))).value;
                            jsonTemplate.textboxes[index]['font'] = document.getElementById(("font" + (index + 1))).value;
                            jsonTemplate.textboxes[index]['justify'] = document.getElementById(("justify" + (index + 1))).value;
                            jsonTemplate.textboxes[index]['concat'] = document.getElementById(("concat" + (index + 1))).value;
                            jsonTemplate.textboxes[index]['outline'] = document.getElementById(("outline" + (index + 1))).value;

                        }

                        console.log(JSON.stringify(jsonTemplate, null, 2));

                    }

                }
            }
        },

        handleMouseOut: function (e) {
            // tell the browser we're handling this event
            e.preventDefault();
            e.stopPropagation();

            mouseX = parseInt(e.clientX - recOffsetX);
            mouseY = parseInt(e.clientY - recOffsetY);

            // Put your mouseOut stuff here
            isRecDown = false;
        },

        handleMouseMove: function (e) {
            if (!isRecDown) {
                return;
            }
            // tell the browser we're handling this event
            e.preventDefault();
            e.stopPropagation();

            mouseX = parseInt(e.clientX - recOffsetX);
            mouseY = parseInt(e.clientY - recOffsetY);
            newRect = {
                left: Math.min(startX, mouseX),
                right: Math.max(startX, mouseX),
                top: Math.min(startY, mouseY),
                bottom: Math.max(startY, mouseY),
                color: "#000000"
            }
            drawRectangleOnCanvas.drawAll();
            context.strokeStyle = "#000000";
            context.lineWidth = strokeWidth;
            context.globalAlpha = 1;
            context.strokeRect(startX, startY, mouseX - startX, mouseY - startY);
        },

    }



}

