function goToListMemesPage() {
    let guild = document.getElementById('guildIdTempVar').innerHTML
    var url = "http://localhost:5000/edit/" + guild + "/memes"
    window.location.href = url;
}


function goToNewMemePage() {
    let guild = document.getElementById('guildIdTempVar').innerHTML
    var url = "http://localhost:5000/build/" + guild + "/new"
    window.location.href = url;
}

// main function for edit meme template page
// get passed here by list all memes page
// or you can go to it dynamically
function loadMemeToUpdate() {
    document.getElementById('updateExistingMemeForm').hidden = false;

    const otherParam = {
        headers: {
            "content-type": "application/json; charset=UTF-8"
        },
        method: "GET"
    };

    let guild = document.getElementById('guildIdTempVar').innerHTML
    let template = document.getElementById('templateIdTempVar').innerHTML

    const baseUrl = 'http://localhost:5000/api/';
    fetch((baseUrl + guild + "/memes/" + template), otherParam)
        .then(data => { return data.json() })
        .then(res => {
            console.log("response from api:")
            console.log(res)

            document.getElementById('imageNameUpdate').value = res['image_url']
            document.getElementById('descriptionValueUpdate').value = res['description']
            document.getElementById('docsValueUpdate').value = res['docs']
            document.getElementById('templateNameValueUpdate').value = res['name']

            buildExisitngMeme(res);

        })
        .catch(error => console.log(error));
}

function switchToNewMeme() {
    document.getElementById('makeNewMeme').hidden = false;
}


// main function for list all memes page..
// hits api with guild id to get list of memes (and their objs)
// builds those into a table
function loadListOfMemes() {

    const otherParam = {
        headers: {
            "content-type": "application/json; charset=UTF-8"
        },
        method: "GET"
    };

    let guild = window.location.hash.replace('#','')
    fetch(`/api/${guild}/memes`, otherParam)
        .then(res => res.json())
        .then(memes => {
            render_meme_list(memes, guild)
        })
        .catch(error => console.log(error));
}


function render_meme_list(memes, guild) {
    document.getElementById("memes").innerHTML = memes.map(m => 
        `<div class="meme" data-link="edit#${guild}/${m.name}">
            <div class="info">
                <span class="name">${m.name}</span>
                <span class="description">${m.description}</span>
            </div>
            <img class="preview" src="${m.image_url}" alt="${m.name}" width="100" height="100">
        </div>`
    ).join("")
}

// insert rows of memes from guild dynamically into table
function insRows(res, guild_id) {
    var data = res
    //var totalColumns = Object.keys(data[0]).length;
    var totalColumns = 3;
    var columnNames = [];
    columnNames = ["Name", "Description", "Image"]
    
    //Create a HTML Table element.
    var table = document.createElement("TABLE");
    table.border = "1";
    
    //Add the header row.
    var row = table.insertRow(-1);
    for (var i = 0; i < totalColumns; i++) {
      var headerCell = document.createElement("TH");
      headerCell.innerHTML = columnNames[i];
      row.appendChild(headerCell);
    }
    
    // Add the data rows.
    for (var i = 0; i < data.length; i++) {
      row = table.insertRow(-1);

      var cell = row.insertCell(-1);
      var name = data[i]['name'];
      var link = "http://localhost:5000/edit/" + guild_id + "/update-template/" + name
      var returned = '<a href="' + link + '">' + name + '</a>';
      cell.innerHTML = returned;
      var cell = row.insertCell(-1);
      cell.innerHTML = data[i]['description'];
      var cell = row.insertCell(-1);
      var image = data[i]['image_url'];
      var image_html =  '<img src="' + image + '" alt="' + name + '" width="100" height="100">'
      cell.innerHTML = image_html

    }
    
    var dvTable = document.getElementById("dvTable");
    dvTable.innerHTML = "";
    dvTable.appendChild(table);
}




/// fix this its dumb
function getJson(boxes2, canvas_width, canvas_hight) {
    var textboxes = [];
    textboxes = boxes2;
    var jsonTemplate = {};
    var temp_json_push = {};

    jsonTemplate["description"] = document.getElementById('descriptionValue').value;
    jsonTemplate["docs"] = document.getElementById('docsValue').value;;
    jsonTemplate["image_url"] = document.getElementById('imagename').value;
    jsonTemplate["layout"] = (document.getElementById('templateNameValue').value + "_layout");
    jsonTemplate["usage"] = 0;
    jsonTemplate["textboxes"] = [];
    jsonTemplate["name"] = document.getElementById('templateNameValue').value;


    textboxes.forEach(addTextboxData)

    function addTextboxData(item, index) {
        temp_json_push = {
            "left": (textboxes[index]['x'] / canvas_width).toFixed(3),
            "top": (textboxes[index]['y'] / canvas_hight).toFixed(3),
            "right": ((textboxes[index]['x'] + textboxes[index]['w']) / canvas_width).toFixed(3),
            "bottom": ((textboxes[index]['y'] + textboxes[index]['h']) / canvas_hight).toFixed(3),
            "color": document.getElementById(("color" + (index + 1))).value,
            "font": document.getElementById(("font" + (index + 1))).value,
            "justify": document.getElementById(("justify" + (index + 1))).value,
            "max_font_size": document.getElementById(("max_font_size" + (index + 1))).value,
            "outline": document.getElementById(("outline" + (index + 1))).value
        }
        jsonTemplate.textboxes.push(temp_json_push);
    }

    return jsonTemplate
}









function getJsonUpdated(boxes2, canvas_width, canvas_hight) {
    var textboxes = [];
    textboxes = boxes2;
    var jsonTemplate = {};
    var temp_json_push = {};

    jsonTemplate["description"] = document.getElementById('descriptionValueUpdate').value;
    jsonTemplate["docs"] = document.getElementById('docsValueUpdate').value;;
    jsonTemplate["image_url"] = document.getElementById('imageNameUpdate').value;
    jsonTemplate["layout"] = (document.getElementById('templateNameValueUpdate').value + "_layout");
    jsonTemplate["usage"] = 0;
    jsonTemplate["textboxes"] = [];
    jsonTemplate["name"] = document.getElementById('templateNameValueUpdate').value;


    textboxes.forEach(addTextboxData)

    function emptyString (value) {

        if (value == "") {
            return null
        }
    }

    function addTextboxData(item, index) {
        temp_json_push = {
            "left": (textboxes[index]['x'] / canvas_width).toFixed(3),
            "top": (textboxes[index]['y'] / canvas_hight).toFixed(3),
            "right": ((textboxes[index]['x'] + textboxes[index]['w']) / canvas_width).toFixed(3),
            "bottom": ((textboxes[index]['y'] + textboxes[index]['h']) / canvas_hight).toFixed(3),
            "color": document.getElementById(("color" + (index + 1))).value,
            "font": document.getElementById(("font" + (index + 1))).value,
            "justify": document.getElementById(("justify" + (index + 1))).value,
            "max_font_size": emptyString(document.getElementById(("max_font_size" + (index + 1))).value),
            "outline": document.getElementById(("outline" + (index + 1))).value
        }
        jsonTemplate.textboxes.push(temp_json_push);
    }

    return jsonTemplate
}






function postJson(json_data) {

    const baseUrl = 'http://localhost:5000/api/';
    var dataBody = JSON.stringify(json_data, null, 2);
    let guild = document.getElementById('guildIdTempVar').innerHTML

    const otherParam = {
        headers: {
            "content-type": "application/json; charset=UTF-8"
        },
        body: dataBody,
        method: "POST"
    };

    fetch((baseUrl + guild + "/save-template/" + json_data['name']), otherParam)
        .then(data => { return data.json() })
        .then(res => { console.log(res) })
        .catch(error => console.log(error));

    alert("The meme template was sent to the database!");
    console.log(JSON.stringify(json_data, null, 2));

}


function getHTMLRow(labelValue, labelForValue, select) {
    var row = document.createElement("div");
    row.setAttribute("class", "row");

    var div = document.createElement("div");
    div.setAttribute("class", "col-25");

    var labelDiv = document.createElement("div");
    labelDiv.setAttribute("class", "col-25");

    var label = document.createElement("label");
    label.setAttribute("for", labelForValue);
    label.innerHTML = labelValue;

    div.appendChild(select);
    labelDiv.appendChild(label)
    row.appendChild(div);
    row.insertBefore(labelDiv, row.firstChild);

    return row
}

function getHTMLSelectOption(value) {
    var option = document.createElement("option");
    option.setAttribute("value", value);
    option.innerHTML = value;

    return option
}

function getHTMLSelectOptionHR(value, humanReadableValue) {
    var option = document.createElement("option");
    option.setAttribute("value", value);
    option.innerHTML = humanReadableValue;

    return option
}


function addDataFields(count, containerName) {
    var drawCount = count + 1;

    var container = document.createElement("div");
    container.setAttribute("class", "container-div");

    // Create new form fields dynamically when every 
    var form = document.createElement("form");
    form.setAttribute("method", "post");

    var textBoxTitleCount = "title" + drawCount;
    var textBoxTitle = document.createElement("h3");
    textBoxTitle.setAttribute("id", textBoxTitleCount);
    textBoxTitle.setAttribute("docId", drawCount);
    textBoxTitle.innerHTML = "Text Box " + drawCount + ":";

    form.appendChild(getHTMLRow("", textBoxTitleCount, textBoxTitle));

    // Create an input element for color

    var colorCount = "color" + drawCount;
    var color = document.createElement("select");
    color.setAttribute("id", colorCount);
    color.setAttribute("docId", drawCount);
    color.appendChild(getHTMLSelectOptionHR("WHITE", "White"));
    color.appendChild(getHTMLSelectOptionHR("BLACK", "Black"));

    // Append the color input to the form 
    form.appendChild(getHTMLRow("Text Color: ", colorCount, color));

    // Create an outline element for justify
    var outlineCount = "outline" + drawCount;
    var outline = document.createElement("select");
    outline.setAttribute("id", outlineCount);
    outline.setAttribute("docId", drawCount);
    outline.appendChild(getHTMLSelectOptionHR("BLACK", "Black"))
    outline.appendChild(getHTMLSelectOptionHR("WHITE", "White"))
    // Append the outline input to the form 
    form.appendChild(getHTMLRow("Outline Color: ", outlineCount, outline));


    // Create an input element for font
    var fontCount = "font" + drawCount;
    var font = document.createElement("select");
    font.setAttribute("id", fontCount);
    font.setAttribute("docId", drawCount);
    // Append the font input to the form 
    font.appendChild(getHTMLSelectOptionHR("IMPACT", "Impact"));
    font.appendChild(getHTMLSelectOptionHR("XKCD", "xkcd"));
    font.appendChild(getHTMLSelectOptionHR("COMIC_SANS", "Comic Sans"));
    form.appendChild(getHTMLRow("Font Type: ", fontCount, font));


    // Create an input element for justify
    var justifyCount = "justify" + drawCount;
    var justify = document.createElement("select");
    justify.setAttribute("id", justifyCount);
    justify.setAttribute("docId", drawCount);
    // Append the justify input to the form 
    justify.appendChild(getHTMLSelectOptionHR("CENTER", "Center"));
    justify.appendChild(getHTMLSelectOptionHR("RIGHT", "Right"));
    justify.appendChild(getHTMLSelectOptionHR("LEFT", "Left"));
    form.appendChild(getHTMLRow("Justification: ", justifyCount, justify));


    // Create an max_font_size element for justify
    var max_font_sizeCount = "max_font_size" + drawCount;
    var max_font_size = document.createElement("input");
    max_font_size.setAttribute("id", max_font_sizeCount);
    max_font_size.setAttribute("docId", drawCount);
    // Append the max_font_size input to the form 
    form.appendChild(getHTMLRow("Max Font Size (Optional): ", max_font_sizeCount, max_font_size));

    if (drawCount == 1) {
        // create a submit button 
        var s = document.createElement("input");
        s.setAttribute("type", "button");
        s.setAttribute("id", "submitButton");
        //s.setAttribute("onClick", "getJSON()")
        s.setAttribute("value", "Save Meme Template");

        // Append the submit button to the form 
        container.appendChild(s);

    }

    container.appendChild(form);

    document.getElementsByClassName(containerName)[0]
        .appendChild(container);



}
























































function buildExisitngMeme(templateJson) {


    (function (window) {

        // Initiate base image for meme in background
        var base_image = new Image();
        // holds all our boxes
        var boxes2 = [];

        // New, holds the 8 tiny boxes that will be our selection handles
        // the selection handles will be in this order:
        // 0  1  2
        // 3     4
        // 5  6  7
        var selectionHandles = [];

        // Hold canvas information
        var canvas;
        var ctx;
        var WIDTH;
        var HEIGHT;
        var INTERVAL = 20;  // how often, in milliseconds, we check to see if a redraw is needed

        var isDrag = false;
        var isResizeDrag = false;
        var expectResize = -1; // New, will save the # of the selection handle if the mouse is over one.
        var mx, my; // mouse coordinates

        // when set to true, the canvas will redraw everything
        // invalidate() just sets this to false right now
        // we want to call invalidate() whenever we make a change
        var canvasValid = false;

        // The node (if any) being selected.
        // If in the future we want to select multiple objects, this will get turned into an array
        var mySel = null;

        // The selection color and width. Right now we have a red selection with a small width
        var mySelColor = '#CC0000';
        var mySelWidth = 4;
        var mySelBoxColor = 'black'; // New for selection boxes
        var mySelBoxSize = 8;

        // we use a fake canvas to draw individual shapes for selection testing
        var ghostcanvas;
        var gctx; // fake canvas context

        // since we can drag from anywhere in a node
        // instead of just its x/y corner, we need to save
        // the offset of the mouse when we start dragging.
        var offsetx, offsety;

        // Padding and border style widths for mouse offsets
        var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop;

        let maxx = 400,
            maxy = 500;

        let ratio = null;

        // Box object to hold data
        function Box2() {
            this.x = 0;
            this.y = 0;
            this.w = 1; // default width and height?
            this.h = 1;
            this.fill = '#444444';
        }

        // New methods on the Box class
        Box2.prototype = {
            // we used to have a solo draw function
            // but now each box is responsible for its own drawing
            // mainDraw() will call this with the normal canvas
            // myDown will call this with the ghost canvas with 'black'
            draw: function (context, optionalColor) {
                if (context === gctx) {
                    context.fillStyle = 'black'; // always want black for the ghost canvas
                } else {
                    context.fillStyle = this.fill;
                }

                // We can skip the drawing of elements that have moved off the screen:
                if (this.x > WIDTH || this.y > HEIGHT) return;
                if (this.x + this.w < 0 || this.y + this.h < 0) return;

                context.fillRect(this.x, this.y, this.w, this.h);

                // draw selection
                // this is a stroke along the box and also 8 new selection handles
                if (mySel === this) {
                    context.strokeStyle = mySelColor;
                    context.lineWidth = mySelWidth;
                    context.strokeRect(this.x, this.y, this.w, this.h);

                    // draw the boxes

                    var half = mySelBoxSize / 2;

                    // 0  1  2
                    // 3     4
                    // 5  6  7

                    // top left, middle, right
                    selectionHandles[0].x = this.x - half;
                    selectionHandles[0].y = this.y - half;

                    selectionHandles[1].x = this.x + this.w / 2 - half;
                    selectionHandles[1].y = this.y - half;

                    selectionHandles[2].x = this.x + this.w - half;
                    selectionHandles[2].y = this.y - half;

                    //middle left
                    selectionHandles[3].x = this.x - half;
                    selectionHandles[3].y = this.y + this.h / 2 - half;

                    //middle right
                    selectionHandles[4].x = this.x + this.w - half;
                    selectionHandles[4].y = this.y + this.h / 2 - half;

                    //bottom left, middle, right
                    selectionHandles[6].x = this.x + this.w / 2 - half;
                    selectionHandles[6].y = this.y + this.h - half;

                    selectionHandles[5].x = this.x - half;
                    selectionHandles[5].y = this.y + this.h - half;

                    selectionHandles[7].x = this.x + this.w - half;
                    selectionHandles[7].y = this.y + this.h - half;


                    context.fillStyle = mySelBoxColor;
                    for (var i = 0; i < 8; i++) {
                        var cur = selectionHandles[i];
                        context.fillRect(cur.x, cur.y, mySelBoxSize, mySelBoxSize);
                    }
                }

            } // end draw

        }

        //Initialize a new Box, add it, and invalidate the canvas
        function addRect(x, y, w, h, fill) {
            var rect = new Box2;
            rect.x = x;
            rect.y = y;
            rect.w = w
            rect.h = h;
            rect.fill = fill;
            boxes2.push(rect);
            invalidate();
        }

        // initialize our canvas, add a ghost canvas, set draw loop
        // then add everything we want to intially exist on the canvas
        function init2() {

            base_image.src = document.getElementById('imageNameUpdate').value; //Load Image ;
            canvas = document.getElementById('canvasExistingMeme');

            ratio = maxx / maxy > base_image.height / base_image.width
                ? maxx / base_image.height
                : maxy / base_image.width

            canvas.width = base_image.width * ratio;
            canvas.height = base_image.height * ratio;

            HEIGHT = canvas.height;
            WIDTH = canvas.width;
            ctx = canvas.getContext('2d');

            ghostcanvas = document.createElement('canvas');
            ghostcanvas.height = HEIGHT;
            ghostcanvas.width = WIDTH;
            gctx = ghostcanvas.getContext('2d');

            // once we get the image, unhide the canvas
            base_image.onload = function () {
                document.getElementById('canvasExistingMeme').hidden = false;
                ctx.drawImage(base_image, 0, 0, base_image.width * ratio, base_image.height * ratio);
            }

            //fixes a problem where double clicking causes text to get selected on the canvas
            canvas.onselectstart = function () { return false; }

            // fixes mouse co-ordinate problems when there's a border or padding
            // see getMouse for more detail
            if (document.defaultView && document.defaultView.getComputedStyle) {
                stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingLeft'], 10) || 0;
                stylePaddingTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingTop'], 10) || 0;
                styleBorderLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderLeftWidth'], 10) || 0;
                styleBorderTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderTopWidth'], 10) || 0;
            }

            // make mainDraw() fire every INTERVAL milliseconds
            setInterval(mainDraw, INTERVAL);

            // set our events. Up and down are for dragging,
            // double click is for making new boxes
            canvas.onmousedown = myDown;
            canvas.onmouseup = myUp;
            canvas.ondblclick = myDblClick;
            canvas.onmousemove = myMove;

            // set up the selection handle boxes
            for (var i = 0; i < 8; i++) {
                var rect = new Box2;
                selectionHandles.push(rect);
            }

            // add textbox initialization here:
            templateJson.textboxes.forEach(addExistingRect)


            //left": (textboxes[index]['x'] / canvas_width).toFixed(3),
            //"top": (textboxes[index]['y'] / canvas_hight).toFixed(3),
            //"right": ((textboxes[index]['x'] + textboxes[index]['w']) / canvas_width).toFixed(3),
            //"bottom": ((textboxes[index]['y'] + textboxes[index]['h']) / canvas_hight).toFixed(3),

            function addExistingRect(item, index) {

                let x = (templateJson.textboxes[index]['left'] * WIDTH)
                let y = (templateJson.textboxes[index]['top'] * HEIGHT)
                let w = ((templateJson.textboxes[index]['right'] * WIDTH) - x)
                let h = ((templateJson.textboxes[index]['bottom'] * HEIGHT) - y)

                addRect(x, y, w, h, 'rgba(0,205,0,0.7)');

                addDataFields(index, "container additionalfieldsUpdate")

            }

            // THIS IS A CHEAT because there is a bug i dont want to figure out right now
            canvas.click()
            // figure it out at some point


            console.log(boxes2.length)

            //addRect(260, 70, 60, 65, 'rgba(0,205,0,0.7)');

            // add a green-blue rectangle
            //addRect(240, 120, 40, 40, 'rgba(2,165,165,0.7)');  

            // add a smaller purple rectangle
            //addRect(45, 60, 25, 25, 'rgba(150,150,250,0.7)');

        }


        //wipes the canvas context
        function clear(c) {
            c.clearRect(0, 0, WIDTH, HEIGHT);
        }

        // Main draw loop.
        // While draw is called as often as the INTERVAL variable demands,
        // It only ever does something if the canvas gets invalidated by our code
        function mainDraw() {
            if (canvasValid == false) {
                clear(ctx);

                // Add stuff you want drawn in the background all the time here
                ctx.drawImage(base_image, 0, 0, base_image.width * ratio, base_image.height * ratio)

                // draw all boxes
                var l = boxes2.length;
                for (var i = 0; i < l; i++) {
                    boxes2[i].draw(ctx); // we used to call drawshape, but now each box draws itself
                }

                // Add stuff you want drawn on top all the time here

                canvasValid = true;
            }

            // Post json data to API here after dynamicall building the json data
            if (boxes2.length != 0) {
                document.getElementById('submitButton').onclick = function () {
                    postJson(getJsonUpdated(boxes2, WIDTH, HEIGHT));
                }
            }
        }

        // Happens when the mouse is moving inside the canvas
        function myMove(e) {
            if (isDrag) {
                getMouse(e);

                mySel.x = mx - offsetx;
                mySel.y = my - offsety;

                // something is changing position so we better invalidate the canvas!
                invalidate();
            } else if (isResizeDrag) {
                // time ro resize!
                var oldx = mySel.x;
                var oldy = mySel.y;

                // 0  1  2
                // 3     4
                // 5  6  7
                switch (expectResize) {
                    case 0:
                        mySel.x = mx;
                        mySel.y = my;
                        mySel.w += oldx - mx;
                        mySel.h += oldy - my;
                        break;
                    case 1:
                        mySel.y = my;
                        mySel.h += oldy - my;
                        break;
                    case 2:
                        mySel.y = my;
                        mySel.w = mx - oldx;
                        mySel.h += oldy - my;
                        break;
                    case 3:
                        mySel.x = mx;
                        mySel.w += oldx - mx;
                        break;
                    case 4:
                        mySel.w = mx - oldx;
                        break;
                    case 5:
                        mySel.x = mx;
                        mySel.w += oldx - mx;
                        mySel.h = my - oldy;
                        break;
                    case 6:
                        mySel.h = my - oldy;
                        break;
                    case 7:
                        mySel.w = mx - oldx;
                        mySel.h = my - oldy;
                        break;
                }

                invalidate();
            }

            getMouse(e);
            // if there's a selection see if we grabbed one of the selection handles
            if (mySel !== null && !isResizeDrag) {
                for (var i = 0; i < 8; i++) {
                    // 0  1  2
                    // 3     4
                    // 5  6  7

                    var cur = selectionHandles[i];

                    // we dont need to use the ghost context because
                    // selection handles will always be rectangles
                    if (mx >= cur.x && mx <= cur.x + mySelBoxSize &&
                        my >= cur.y && my <= cur.y + mySelBoxSize) {
                        // we found one!
                        expectResize = i;
                        invalidate();

                        switch (i) {
                            case 0:
                                this.style.cursor = 'nw-resize';
                                break;
                            case 1:
                                this.style.cursor = 'n-resize';
                                break;
                            case 2:
                                this.style.cursor = 'ne-resize';
                                break;
                            case 3:
                                this.style.cursor = 'w-resize';
                                break;
                            case 4:
                                this.style.cursor = 'e-resize';
                                break;
                            case 5:
                                this.style.cursor = 'sw-resize';
                                break;
                            case 6:
                                this.style.cursor = 's-resize';
                                break;
                            case 7:
                                this.style.cursor = 'se-resize';
                                break;
                        }
                        return;
                    }

                }
                // not over a selection box, return to normal
                isResizeDrag = false;
                expectResize = -1;
                this.style.cursor = 'auto';
            }

        }

        // Happens when the mouse is clicked in the canvas
        function myDown(e) {
            getMouse(e);

            //we are over a selection box
            if (expectResize !== -1) {
                isResizeDrag = true;
                return;
            }

            clear(gctx);
            var l = boxes2.length;
            for (var i = l - 1; i >= 0; i--) {
                // draw shape onto ghost context
                boxes2[i].draw(gctx, 'black');

                // get image data at the mouse x,y pixel
                var imageData = gctx.getImageData(mx, my, 1, 1);
                var index = (mx + my * imageData.width) * 4;

                // if the mouse pixel exists, select and break
                if (imageData.data[3] > 0) {
                    mySel = boxes2[i];
                    offsetx = mx - mySel.x;
                    offsety = my - mySel.y;
                    mySel.x = mx - offsetx;
                    mySel.y = my - offsety;
                    isDrag = true;

                    invalidate();
                    clear(gctx);
                    return;
                }

            }
            // havent returned means we have selected nothing
            mySel = null;
            // clear the ghost canvas for next time
            clear(gctx);
            // invalidate because we might need the selection border to disappear
            invalidate();
        }

        function myUp() {
            console.log(boxes2);
            isDrag = false;
            isResizeDrag = false;
            expectResize = -1;
        }

        // adds a new node
        function myDblClick(e) {
            getMouse(e);
            // for this method width and height determine the starting X and Y, too.
            // so I left them as vars in case someone wanted to make them args for something and copy this code

            // ADD IN THE CREATION OF EACH TEXT BOX FIELD DATA FORM HERE

            addDataFields(boxes2.length, "container additionalfieldsUpdate")

            var width = 200;
            var height = 80;
            addRect(mx - (width / 2), my - (height / 2), width, height, 'rgba(220,205,65,0.7)');
        }


        function invalidate() {
            canvasValid = false;
        }

        // Sets mx,my to the mouse position relative to the canvas
        // unfortunately this can be tricky, we have to worry about padding and borders
        function getMouse(e) {
            var element = canvas, offsetX = 0, offsetY = 0;

            if (element.offsetParent) {
                do {
                    offsetX += element.offsetLeft;
                    offsetY += element.offsetTop;
                } while ((element = element.offsetParent));
            }

            // Add padding and border style widths to offset
            offsetX += stylePaddingLeft;
            offsetY += stylePaddingTop;

            offsetX += styleBorderLeft;
            offsetY += styleBorderTop;

            mx = e.pageX - offsetX;
            my = e.pageY - offsetY
        }

        // If you dont want to use <body onLoad='init()'>
        // You could uncomment this init() reference and place the script reference inside the body tag
        //init();
        window.init2 = init2;
    })(window);

    init2();

}















































































































































function buildNewMeme() {

    (function (window) {

        // Initiate base image for meme in background
        var base_image = new Image();
        // holds all our boxes
        var boxes2 = [];

        // New, holds the 8 tiny boxes that will be our selection handles
        // the selection handles will be in this order:
        // 0  1  2
        // 3     4
        // 5  6  7
        var selectionHandles = [];

        // Hold canvas information
        var canvas;
        var ctx;
        var WIDTH;
        var HEIGHT;
        var INTERVAL = 20;  // how often, in milliseconds, we check to see if a redraw is needed

        var isDrag = false;
        var isResizeDrag = false;
        var expectResize = -1; // New, will save the # of the selection handle if the mouse is over one.
        var mx, my; // mouse coordinates

        // when set to true, the canvas will redraw everything
        // invalidate() just sets this to false right now
        // we want to call invalidate() whenever we make a change
        var canvasValid = false;

        // The node (if any) being selected.
        // If in the future we want to select multiple objects, this will get turned into an array
        var mySel = null;

        // The selection color and width. Right now we have a red selection with a small width
        var mySelColor = '#CC0000';
        var mySelWidth = 6;
        var mySelBoxColor = 'black'; // New for selection boxes
        var mySelBoxSize = 10;

        // we use a fake canvas to draw individual shapes for selection testing
        var ghostcanvas;
        var gctx; // fake canvas context

        // since we can drag from anywhere in a node
        // instead of just its x/y corner, we need to save
        // the offset of the mouse when we start dragging.
        var offsetx, offsety;

        // Padding and border style widths for mouse offsets
        var stylePaddingLeft, stylePaddingTop, styleBorderLeft, styleBorderTop;

        let maxx = 400,
            maxy = 500;

        let ratio = null;

        // Box object to hold data
        function Box2() {
            this.x = 0;
            this.y = 0;
            this.w = 1; // default width and height?
            this.h = 1;
            this.fill = '#444444';
        }

        // New methods on the Box class
        Box2.prototype = {
            // we used to have a solo draw function
            // but now each box is responsible for its own drawing
            // mainDraw() will call this with the normal canvas
            // myDown will call this with the ghost canvas with 'black'
            draw: function (context, optionalColor) {
                if (context === gctx) {
                    context.fillStyle = 'black'; // always want black for the ghost canvas
                } else {
                    context.fillStyle = this.fill;
                }

                // We can skip the drawing of elements that have moved off the screen:
                if (this.x > WIDTH || this.y > HEIGHT) return;
                if (this.x + this.w < 0 || this.y + this.h < 0) return;

                context.fillRect(this.x, this.y, this.w, this.h);

                // draw selection
                // this is a stroke along the box and also 8 new selection handles
                if (mySel === this) {
                    context.strokeStyle = mySelColor;
                    context.lineWidth = mySelWidth;
                    context.strokeRect(this.x, this.y, this.w, this.h);

                    // draw the boxes

                    var half = mySelBoxSize / 2;

                    // 0  1  2
                    // 3     4
                    // 5  6  7
                    //https://jswny.github.io/2ewiki/chris.png
                    //chris neckbeard yummy
                    //https://wiki.2edgy4.me
                    //chris-neck-beard

                    // top left, middle, right
                    selectionHandles[0].x = this.x - half;
                    selectionHandles[0].y = this.y - half;

                    selectionHandles[1].x = this.x + this.w / 2 - half;
                    selectionHandles[1].y = this.y - half;

                    selectionHandles[2].x = this.x + this.w - half;
                    selectionHandles[2].y = this.y - half;

                    //middle left
                    selectionHandles[3].x = this.x - half;
                    selectionHandles[3].y = this.y + this.h / 2 - half;

                    //middle right
                    selectionHandles[4].x = this.x + this.w - half;
                    selectionHandles[4].y = this.y + this.h / 2 - half;

                    //bottom left, middle, right
                    selectionHandles[6].x = this.x + this.w / 2 - half;
                    selectionHandles[6].y = this.y + this.h - half;

                    selectionHandles[5].x = this.x - half;
                    selectionHandles[5].y = this.y + this.h - half;

                    selectionHandles[7].x = this.x + this.w - half;
                    selectionHandles[7].y = this.y + this.h - half;


                    context.fillStyle = mySelBoxColor;
                    for (var i = 0; i < 8; i++) {
                        var cur = selectionHandles[i];
                        context.fillRect(cur.x, cur.y, mySelBoxSize, mySelBoxSize);
                    }
                }

            } // end draw

        }

        //Initialize a new Box, add it, and invalidate the canvas
        function addRect(x, y, w, h, fill) {
            var rect = new Box2;
            rect.x = x;
            rect.y = y;
            rect.w = w
            rect.h = h;
            rect.fill = fill;
            boxes2.push(rect);
            invalidate();
        }

        // initialize our canvas, add a ghost canvas, set draw loop
        // then add everything we want to intially exist on the canvas
        function init2() {

            base_image.src = document.getElementById('imagename').value; //Load Image ;
            canvas = document.getElementById('canvasNewMeme');

            ratio = maxx / maxy > base_image.height / base_image.width
                ? maxx / base_image.height
                : maxy / base_image.width

            canvas.width = base_image.width * ratio;
            canvas.height = base_image.height * ratio;

            HEIGHT = canvas.height;
            WIDTH = canvas.width;
            ctx = canvas.getContext('2d');

            ghostcanvas = document.createElement('canvas');
            ghostcanvas.height = HEIGHT;
            ghostcanvas.width = WIDTH;
            gctx = ghostcanvas.getContext('2d');

            // once we get the image, unhide the canvas
            base_image.onload = function () {
                document.getElementById('canvasNewMeme').hidden = false;
                ctx.drawImage(base_image, 0, 0, base_image.width * ratio, base_image.height * ratio);
            }

            //fixes a problem where double clicking causes text to get selected on the canvas
            canvas.onselectstart = function () { return false; }

            // fixes mouse co-ordinate problems when there's a border or padding
            // see getMouse for more detail
            if (document.defaultView && document.defaultView.getComputedStyle) {
                stylePaddingLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingLeft'], 10) || 0;
                stylePaddingTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['paddingTop'], 10) || 0;
                styleBorderLeft = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderLeftWidth'], 10) || 0;
                styleBorderTop = parseInt(document.defaultView.getComputedStyle(canvas, null)['borderTopWidth'], 10) || 0;
            }

            // make mainDraw() fire every INTERVAL milliseconds
            setInterval(mainDraw, INTERVAL);

            // set our events. Up and down are for dragging,
            // double click is for making new boxes
            canvas.onmousedown = myDown;
            canvas.onmouseup = myUp;
            canvas.ondblclick = myDblClick;
            canvas.onmousemove = myMove;

            // set up the selection handle boxes
            for (var i = 0; i < 8; i++) {
                var rect = new Box2;
                selectionHandles.push(rect);
            }

            // add custom initialization here:

        }


        //wipes the canvas context
        function clear(c) {
            c.clearRect(0, 0, WIDTH, HEIGHT);
        }

        // Main draw loop.
        // While draw is called as often as the INTERVAL variable demands,
        // It only ever does something if the canvas gets invalidated by our code
        function mainDraw() {
            if (canvasValid == false) {
                clear(ctx);

                // Add stuff you want drawn in the background all the time here
                ctx.drawImage(base_image, 0, 0, base_image.width * ratio, base_image.height * ratio)

                // draw all boxes
                var l = boxes2.length;
                for (var i = 0; i < l; i++) {
                    boxes2[i].draw(ctx); // we used to call drawshape, but now each box draws itself
                }

                // Add stuff you want drawn on top all the time here

                canvasValid = true;
            }

            // Post json data to API here after dynamicall building the json data
            if (boxes2.length != 0) {
                document.getElementById('submitButton').onclick = function () {
                    postJson(getJson(boxes2, WIDTH, HEIGHT));
                }
            }
        }

        // Happens when the mouse is moving inside the canvas
        function myMove(e) {
            if (isDrag) {
                getMouse(e);

                mySel.x = mx - offsetx;
                mySel.y = my - offsety;

                // something is changing position so we better invalidate the canvas!
                invalidate();
            } else if (isResizeDrag) {
                // time ro resize!
                var oldx = mySel.x;
                var oldy = mySel.y;

                // 0  1  2
                // 3     4
                // 5  6  7
                switch (expectResize) {
                    case 0:
                        mySel.x = mx;
                        mySel.y = my;
                        mySel.w += oldx - mx;
                        mySel.h += oldy - my;
                        break;
                    case 1:
                        mySel.y = my;
                        mySel.h += oldy - my;
                        break;
                    case 2:
                        mySel.y = my;
                        mySel.w = mx - oldx;
                        mySel.h += oldy - my;
                        break;
                    case 3:
                        mySel.x = mx;
                        mySel.w += oldx - mx;
                        break;
                    case 4:
                        mySel.w = mx - oldx;
                        break;
                    case 5:
                        mySel.x = mx;
                        mySel.w += oldx - mx;
                        mySel.h = my - oldy;
                        break;
                    case 6:
                        mySel.h = my - oldy;
                        break;
                    case 7:
                        mySel.w = mx - oldx;
                        mySel.h = my - oldy;
                        break;
                }

                invalidate();
            }

            getMouse(e);
            // if there's a selection see if we grabbed one of the selection handles
            if (mySel !== null && !isResizeDrag) {
                for (var i = 0; i < 8; i++) {
                    // 0  1  2
                    // 3     4
                    // 5  6  7

                    var cur = selectionHandles[i];

                    // we dont need to use the ghost context because
                    // selection handles will always be rectangles
                    if (mx >= cur.x && mx <= cur.x + mySelBoxSize &&
                        my >= cur.y && my <= cur.y + mySelBoxSize) {
                        // we found one!
                        expectResize = i;
                        invalidate();

                        switch (i) {
                            case 0:
                                this.style.cursor = 'nw-resize';
                                break;
                            case 1:
                                this.style.cursor = 'n-resize';
                                break;
                            case 2:
                                this.style.cursor = 'ne-resize';
                                break;
                            case 3:
                                this.style.cursor = 'w-resize';
                                break;
                            case 4:
                                this.style.cursor = 'e-resize';
                                break;
                            case 5:
                                this.style.cursor = 'sw-resize';
                                break;
                            case 6:
                                this.style.cursor = 's-resize';
                                break;
                            case 7:
                                this.style.cursor = 'se-resize';
                                break;
                        }
                        return;
                    }

                }
                // not over a selection box, return to normal
                isResizeDrag = false;
                expectResize = -1;
                this.style.cursor = 'auto';
            }

        }

        // Happens when the mouse is clicked in the canvas
        function myDown(e) {
            getMouse(e);

            //we are over a selection box
            if (expectResize !== -1) {
                isResizeDrag = true;
                return;
            }

            clear(gctx);
            var l = boxes2.length;
            for (var i = l - 1; i >= 0; i--) {
                // draw shape onto ghost context
                boxes2[i].draw(gctx, 'black');

                // get image data at the mouse x,y pixel
                var imageData = gctx.getImageData(mx, my, 1, 1);
                var index = (mx + my * imageData.width) * 4;

                // if the mouse pixel exists, select and break
                if (imageData.data[3] > 0) {
                    mySel = boxes2[i];
                    offsetx = mx - mySel.x;
                    offsety = my - mySel.y;
                    mySel.x = mx - offsetx;
                    mySel.y = my - offsety;
                    isDrag = true;

                    invalidate();
                    clear(gctx);
                    return;
                }

            }
            // havent returned means we have selected nothing
            mySel = null;
            // clear the ghost canvas for next time
            clear(gctx);
            // invalidate because we might need the selection border to disappear
            invalidate();
        }

        function myUp() {

            // ADD IN the updating of fields here


            console.log(boxes2);
            isDrag = false;
            isResizeDrag = false;
            expectResize = -1;
        }

        // adds a new node
        function myDblClick(e) {
            getMouse(e);
            // for this method width and height determine the starting X and Y, too.
            // so I left them as vars in case someone wanted to make them args for something and copy this code

            // ADD IN THE CREATION OF EACH TEXT BOX FIELD DATA FORM HERE

            addDataFields(boxes2.length, "container additionalfields")

            var width = 200;
            var height = 80;
            addRect(mx - (width / 2), my - (height / 2), width, height, 'rgba(220,205,65,0.7)');
        }


        function invalidate() {
            canvasValid = false;
        }

        // Sets mx,my to the mouse position relative to the canvas
        // unfortunately this can be tricky, we have to worry about padding and borders
        function getMouse(e) {
            var element = canvas, offsetX = 0, offsetY = 0;

            if (element.offsetParent) {
                do {
                    offsetX += element.offsetLeft;
                    offsetY += element.offsetTop;
                } while ((element = element.offsetParent));
            }

            // Add padding and border style widths to offset
            offsetX += stylePaddingLeft;
            offsetY += stylePaddingTop;

            offsetX += styleBorderLeft;
            offsetY += styleBorderTop;

            mx = e.pageX - offsetX;
            my = e.pageY - offsetY
        }

        // If you dont want to use <body onLoad='init()'>
        // You could uncomment this init() reference and place the script reference inside the body tag
        //init();
        window.init2 = init2;
    })(window);

    init2();

}