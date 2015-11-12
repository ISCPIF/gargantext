
function pr(msg) {
    console.log(msg)
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


var latest,oldest;

var TheBuffer = false

var PossibleActions = [
	{
	  "id":"delete",
	  "name": "Delete",
	  "color":"red"
	}, 
	{
	  "id":"keep",
	  "name": "Keep",
	  "color":"green"
	}, 
	// {
	//   "id":"to_group",
	//   "name": "Group",
	//   "color":"blue"
	// }
]

var GState = 0
var System = {
	// 1: {
	// },
	0: {
		"states" : [ "normal" , "keep" , "delete" , "group"] ,
		"statesD" : {} ,
		"dict" : {
			"normal": {
			  "id":"normal",
			  "name": "Normal",
			  "color":"black"
			}, 
			"delete": {
			  "id":"delete",
			  "name": "Delete",
			  "color":"red"
			}, 
			"keep": {
			  "id":"keep",
			  "name": "Keep",
			  "color":"green"
			}, 
			"group": {
			  "id":"group",
			  "name": "MainForm",
			  "color":"white"
			}
		}
	}
	
}

for(var i in System[GState]["states"] ) {
	System[GState]["statesD"][ System[GState]["states"][i] ] = Number(i)
}


var FlagsBuffer = {}
for(var i in System[GState]["states"]) {
  FlagsBuffer[System[GState]["states"][i]] = {}
}


var MyTable;
var RecDict={};
var AjaxRecords = []

//      D3.js: Interactive timerange variables.
var LineChart = dc.lineChart("#monthly-move-chart"); 
var volumeChart = dc.barChart("#monthly-volume-chart");



function Push2Buffer( NewVal ) {
    if ( TheBuffer == false) {
        if( ! NewVal ) {
            var limits = [ oldest , latest ];
            NewVal = limits;
        }
        console.log( " - - - - - - " )
        console.log( "\tchanging to:" )
        console.log( NewVal )
        TheBuffer = NewVal;
        Final_UpdateTable( "changerange" )
        console.log( "- - - - - - -\n" )
        return 1;
    }

    if ( TheBuffer != false ) {
        var past = TheBuffer[0]+"_"+TheBuffer[1]

        if( ! NewVal ) {
            var limits = [ oldest , latest ];
            NewVal = limits;
        }
        var now = NewVal[0]+"_"+NewVal[1]
        
        if ( past != now ) {
            console.log( " - - - - - - " )
            console.log( "\tchanging to:" )
            console.log( NewVal )
            TheBuffer = NewVal;
            Final_UpdateTable( "changerange" )
            console.log( "- - - - - - -\n" )
        }
        return 1;
    }
}

function Final_UpdateTable( action ) {
    // (1) Identifying if the button is collapsed:   
    var isCollapsed=false;
    var accordiontext = $("#collapseOne").attr("class")
    if(accordiontext.indexOf("collapse in")>-1) 
        isCollapsed=true;


    var UpdateTable = false
    if ( (action == "click" && !isCollapsed) || (action=="changerange" && isCollapsed) ) {
        UpdateTable = true;
        $("#corpusdisplayer").html("Close Folder")
    } else $("#corpusdisplayer").html("Open Folder")

    pr("update table??: "+UpdateTable)

    if ( ! UpdateTable ) return false; //stop whatever you wanted to do.



    var TimeRange = AjaxRecords;

    var dataini = (TheBuffer[0])?TheBuffer[0]:oldest;
    var datafin = (TheBuffer[1])?TheBuffer[1]:latest;
    pr("show me the pubs of the selected period")
    pr("\tfrom ["+dataini+"] to ["+datafin+"]")
    pr("\tfrom ["+oldest+"] to ["+latest+"]")

    TimeRange = []
    for (var i in AjaxRecords) {
        if(AjaxRecords[i].score>=dataini && AjaxRecords[i].score<=datafin){
            // pr( AjaxRecords[i].date+" : "+AjaxRecords[i].id )
            TimeRange.push(AjaxRecords[i])
        }
    }
    
    MyTable = $('#my-ajax-table').dynatable({
        dataset: {
            records: TimeRange
        },
        features: {
            pushState: false,
            // sort: false
        },
        writers: {
          _rowWriter: ulWriter
          // _cellWriter: customCellWriter
        }
    });
    MyTable.data('dynatable').settings.dataset.originalRecords = []
    MyTable.data('dynatable').settings.dataset.originalRecords = TimeRange;
    
    MyTable.data('dynatable').paginationPage.set(1);
    MyTable.data('dynatable').process();
}

function getRecord(rec_id) {
  return MyTable.data('dynatable').settings.dataset.originalRecords[rec_id];
  // return AjaxRecords[rec_id]
}

function getRecords() {
  return MyTable.data('dynatable').settings.dataset.originalRecords;
}

function save_groups() {
	var groupdiv = "#group_box"
	var gcontent = groupdiv+"_content"
	var count = 0
	var mainform = -1
	var writeflag = ($("#group_box_content").children('span').length>1)?true:false
		$(gcontent).children('span').each(function () {
			var nid = $(this).data("id");
			if (count==0) {
				if(writeflag) {
					// AjaxRecords[RecDict[nid]].name += "*" 
					FlagsBuffer["group"][ nid ] = []
					mainform = nid
		    		AjaxRecords[RecDict[nid]].state = 1
		    	} else {
		    		AjaxRecords[RecDict[nid]].state = 0;
		    	}
		    } else {
				if(writeflag) {
					FlagsBuffer["group"][ mainform ].push( nid )
		    		AjaxRecords[RecDict[nid]].state = -1
				}
		    }
		    count++
		});
	$("#group_box").remove()
	GState=0
	MyTable.data('dynatable').dom.update();
}

function cancel_groups() {
	var groupdiv = "#group_box"
	var gcontent = groupdiv+"_content"
	$(gcontent).children('span').each(function () {
	    var nid = $(this).data("id");
	    AjaxRecords[RecDict[nid]].state = 0
	});
	$("#group_box").remove()
	GState=0
	MyTable.data('dynatable').dom.update();
}

function add2groupdiv( elem_id ) {
	$('<span/>', {
		"data-id":AjaxRecords[elem_id].id,
		"data-stuff": elem_id,
	    title: 'Click to remove',
	    text: AjaxRecords[elem_id].name,
	    css: {
	    	"cursor":"pointer",
	    	"border": "1px solid blue",
	    	"margin": "3px",
	    	"padding": "3px",
	    }
	})
	.click(function() {
    	AjaxRecords[$(this).data("stuff")].state=0;
    	$(this).remove()
    	// if nothing in group div, then remove it
    	if( $("#group_box_content").children().length==0 ) {
    		$("#group_box").remove()
    		GState=0
    	}
    	MyTable.data('dynatable').dom.update();
	})
	.appendTo('#group_box_content')
	AjaxRecords[elem_id].state=3;// 3: "group" state
}
// new
function add2group ( elem ) {

	if( $("#group_box").length==0 ) {
		var div_name = "#my-ajax-table > thead > tr > th:nth-child(1)"
		var prctg = $(div_name).width()// / $(div_name).parent().width() * 100;
		var group_html =  '      <span class="group_box" style="max-width:'+prctg+'px;" id="group_box">'+'\n';
			group_html += '        <span class="group_box header" id="group_box_header"></span>'+'\n';
			group_html += '        <span class="group_box content" id="group_box_content"></span>'+'\n';
			group_html += '      </span>'+'\n';
			$(group_html).insertAfter( "#my-ajax-table > thead" )
			$("#group_box").append  ('<span onclick="save_groups()"> [ Ok</span> - <span onclick="cancel_groups()">No ] </span>')
	}
	GState=1

	var elem_id = $( elem ).data("stuff")
	add2groupdiv( elem_id )
	if( FlagsBuffer["group"][ AjaxRecords[elem_id].id ] ) {
		for(var i in FlagsBuffer["group"][ AjaxRecords[elem_id].id ] ) {
			var nodeid = FlagsBuffer["group"][ AjaxRecords[elem_id].id ][i]
			add2groupdiv ( RecDict[ nodeid ] )
		}
	}

	delete FlagsBuffer["group"][ AjaxRecords[elem_id].id ]

	MyTable.data('dynatable').dom.update();
}

// new
// click red, click keep, click normal...
function clickngram_action ( elem ) {
	var elem_id = $( elem ).data("stuff")
	AjaxRecords[elem_id].state = (AjaxRecords[elem_id].state==(System[0]["states"].length-2))?0:(AjaxRecords[elem_id].state+1);

	MyTable.data('dynatable').dom.update();
}

// function YOLO() {

//   var sum__selected_elems = 0;

//   for(var i in FlagsBuffer["group"])
//   	sum__selected_elems += Object.keys( FlagsBuffer["group"][i] ).length
//   for(var i in FlagsBuffer)
//     sum__selected_elems += Object.keys(FlagsBuffer[i]).length;

//   console.log("")
//   console.log("Current Buffer size: "+sum__selected_elems)
//   console.log(FlagsBuffer)

//   if ( sum__selected_elems>0 )
//     $("#Clean_All, #Save_All").removeAttr("disabled", "disabled");
//   else 
//     $("#Clean_All, #Save_All").attr( "disabled", "disabled" );
// }


// modified
function transformContent(rec_id) {
	var elem = AjaxRecords[rec_id];
	var result = {}
	var atts = System[0]["dict"][ System[0]["states"][elem.state] ]
	var plus_event = ""
	if(GState==0 && elem.state!=System[0]["statesD"]["delete"] ) // if deleted, no + button
		plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(+)</a>"
	if(GState==1 ) {
		if(elem.state!=System[0]["statesD"]["delete"] && elem.state!=System[0]["statesD"]["group"]) { // if deleted and already group, no Up button
			plus_event = " <a class=\"plusclass\" onclick=\"add2group(this.parentNode.parentNode)\">(▲)</a>"
		}
	}
	result["id"] = elem["id"]
	result["score"] = '<span class="'+atts.id+'">'+elem["score"]+'</span>'
	result["name"] = "<span class=\""+atts.id+
					 "\" onclick=\"clickngram_action(this.parentNode.parentNode)\">"+elem["name"]+"</span>"+
					 plus_event
	return result;
}

// to delete
// Affecting the tr element somehow
function overRide(elem) {
  var id = elem.id
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  var this_newflag = (current_flag==AjaxRecords[id]["flag"])?false:current_flag

  console.log("striking: "+id+" | this-elem_flag: "+AjaxRecords[id]["flag"]+" | current_flag: "+current_flag)
  console.log("\t so the new flag is: "+this_newflag)
  // if(this_newflag)
  //   FlagsBuffer[this_newflag][id] = true;
  // else 
  //   delete FlagsBuffer[ AjaxRecords[id]["flag"] ][id];
  AjaxRecords[id]["flag"] = Mark_NGram ( id , AjaxRecords[id]["flag"] , this_newflag );

  var sum__selected_elems = 0;
  for(var i in FlagsBuffer)
    sum__selected_elems += Object.keys(FlagsBuffer[i]).length;

  console.log("")
  console.log("Current Buffer size: "+sum__selected_elems)
  console.log(FlagsBuffer)

  if ( sum__selected_elems>0 )
    $("#Clean_All, #Save_All").removeAttr("disabled", "disabled");
  else 
    $("#Clean_All, #Save_All").attr( "disabled", "disabled" );

  MyTable.data('dynatable').dom.update();

}

// Here you have to put the weird case of Change from Group-Mode
function DeactivateSelectAll() {
  if( $("#multiple_selection").length>0 )
    $("#multiple_selection")[0].checked = false;

  if( Object.keys(FlagsBuffer["to_group"]).length ){


    $("#savemodal").modal("show").css({
        'margin-top': function () { //vertical centering
            console.log($(".modal-content").height())
            return ($(this).height() / 2);
        }
    });

    console.log("OH OH")
    console.log("There are some nodes in group array!:")
    // $("#to_group").html( Object.keys(FlagsBuffer["to_group"]).join(" , ") );
    var labels = []
    for (var i in FlagsBuffer["to_group"]){
      var fake_id = i
      console.log( AjaxRecords[fake_id] )
      labels.push(AjaxRecords[fake_id].name)
    //   $("#to_group").htm
    }

    $("#to_group").html( '<font color="blue">' + labels.join(" , ") + '</div>' );
  }
}


function Mark_NGram( ngram_id , old_flag , new_flag ) {
  if(new_flag){
    for(var f in FlagsBuffer) {
      if( new_flag==f )
        FlagsBuffer[f][ngram_id] = true;
      else 
        delete FlagsBuffer[f][ngram_id];
    }
  } else {
    delete FlagsBuffer[ old_flag ][ngram_id];
  }
  return new_flag;
}


//generic enough
function ulWriter(rowIndex, record, columns, cellWriter) {
  var tr = '';
  var cp_rec = {}

  if( AjaxRecords[RecDict[record.id]].state < 0 )
  	return false;

  cp_rec = transformContent(RecDict[record.id])
  
  // grab the record's attribute for each column
  for (var i = 0, len = columns.length; i < len; i++) {
    tr += cellWriter(columns[i], cp_rec);
  }
  var data_id = RecDict[record.id]
  return '<tr data-stuff='+data_id+'>' + tr + '</tr>';
}

function SelectAll( the_checkbox ) {
  console.log(the_checkbox)
  var current_flag = $("input[type='radio'][name='radios']:checked").val()
  $("tbody tr").each(function (i, row) {
      var id = $(row).data('stuff')
      // AjaxRecords[id]["flag"] = (the_checkbox.checked)?the_flag:false;
      

      var this_newflag = (the_checkbox.checked)?current_flag:false;

      // console.log("striking: "+id+" | this-elem_flag: "+AjaxRecords[id]["flag"]+" | current_flag: "+current_flag)
      // console.log("\t so the new flag is: "+this_newflag)

      AjaxRecords[id]["flag"] = Mark_NGram ( id , AjaxRecords[id]["flag"] , this_newflag );



  });
  MyTable.data('dynatable').dom.update();
}


$("#Clean_All").click(function(){

	for(var id in AjaxRecords)
		AjaxRecords[id]["state"] = 0;

	$("#group_box").remove()
	GState=0

	MyTable.data('dynatable').dom.update();

	for(var i in FlagsBuffer)
		for(var j in FlagsBuffer[i])
			delete FlagsBuffer[i][j];
  // $("#Clean_All, #Save_All").attr( "disabled", "disabled" );

});

$("#Save_All").click(function(){
	console.clear()
	console.log("click in save all 01")
	var sum__selected_elems = 0;

	FlagsBuffer["delete"] = {}
	FlagsBuffer["keep"] = {}
	FlagsBuffer["outmap"] = {}
	FlagsBuffer["inmap"] = {}

	for(var id in AjaxRecords) {
		if( ngrams_map[ AjaxRecords[id]["id"] ] ) {
			if(AjaxRecords[id]["state"]==0 || AjaxRecords[id]["state"]==2) {
				FlagsBuffer["outmap"][ AjaxRecords[id].id ] = true
				if(AjaxRecords[id]["state"]==2) {
					FlagsBuffer["delete"][AjaxRecords[id].id] = true
				}
			}
			if(FlagsBuffer["group"][AjaxRecords[id].id] && AjaxRecords[id]["state"]==1)  {
				FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
			}
		} else {		
			if(AjaxRecords[id]["state"]==1) {
				FlagsBuffer["inmap"][ AjaxRecords[id].id ] = true
			}
			if(AjaxRecords[id]["state"]==2) {
				FlagsBuffer["delete"][AjaxRecords[id].id] = true
			}
		}
	}
	// [ = = = = For deleting subforms = = = = ]
	for(var i in ngrams_groups.links) {
		if(FlagsBuffer["delete"][i]) {
			for(var j in ngrams_groups.links[i] ) {
				FlagsBuffer["delete"][ngrams_groups.links[i][j]] = true
			}
			for(var j in FlagsBuffer["delete"][i] ) {
				FlagsBuffer["delete"][FlagsBuffer["delete"][i][j]] = true
			}
		}
		if(FlagsBuffer["inmap"][i]) {
			for(var j in FlagsBuffer["group"][i] ) {
				FlagsBuffer["outmap"][FlagsBuffer["group"][i][j]] = true
			}
		}
	}
	// [ = = = = / For deleting subforms = = = = ]

	// console.log(" = = = = = = = = = == ")
	// console.log("FlagsBuffer:")
	// console.log(FlagsBuffer)


	var nodes_2del = Object.keys(FlagsBuffer["delete"]).map(Number)
	var nodes_2keep = Object.keys(FlagsBuffer["keep"]).map(Number)
	var nodes_2group = $.extend({}, FlagsBuffer["group"])
	var nodes_2inmap = $.extend({}, FlagsBuffer["inmap"])
	var nodes_2outmap = $.extend({}, FlagsBuffer["outmap"])

	// console.log("")
	// console.log("")
	// console.log(" nodes_2del: ")
	// console.log(nodes_2del)
	// console.log(" nodes_2keep: ")
	// console.log(nodes_2keep)
	// console.log(" nodes_2group: ")
	// console.log(nodes_2group)
	// console.log(" nodes_2inmap: ")
	// console.log(nodes_2inmap)
	// console.log(" nodes_2outmap: ")
	// console.log(nodes_2outmap)
	// console.log("")
	// console.log("")

	var list_id = $("#list_id").val()
	var corpus_id = getIDFromURL( "corpus" ) // not used

	// $.when(
	// ).then(function() {
	// 	// window.location.reload()
	// });

	$("#Save_All").append('<img width="8%" src="/static/img/ajax-loader.gif"></img>')
	CRUD( corpus_id , "/group" , [] , nodes_2group , "PUT" )
	$.doTimeout( 1000, function(){
		CRUD( corpus_id , "/keep" , [] , nodes_2inmap , "PUT" )
		$.doTimeout( 1000, function(){
			CRUD( corpus_id , "/keep" , [] , nodes_2outmap , "DELETE" )
			$.doTimeout( 1000, function(){
				CRUD( list_id , "" , nodes_2del , [] , "DELETE" ),
				$.doTimeout( 1000, function(){
					window.location.reload()
				});
			});
		});
	});

});

function CRUD( parent_id , action , nodes , args , http_method ) {
	var the_url = window.location.origin+"/api/node/"+parent_id+"/ngrams"+action+"/"+nodes.join("+");
	the_url = the_url.replace(/\/$/, ""); //remove trailing slash
	if(nodes.length>0 || Object.keys(args).length>0) {
		$.ajax({
		  method: http_method,
		  url: the_url,
		  data: args,
		  beforeSend: function(xhr) {
		    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
		  },
		  success: function(data){
		  		console.log(http_method + " ok!!")
		        console.log(nodes)
		        console.log(data)
		        return true;
		  },
		  error: function(result) {
		      console.log("Data not found in #Save_All");
		      console.log(result)
		      return false;
		  }
		});

	}
}

function Main_test( data , initial) {


    var DistributionDict = {}
    for(var i in DistributionDict)
        delete DistributionDict[i];
    delete DistributionDict;
    DistributionDict = {}

    AjaxRecords = []

    var FirstScore = initial;

    var arrayd3 = []

    //  div_table += "\t"+"\t"+"\t"+'<input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select'+"\n"
    $("#div-table").html("")
    $("#div-table").empty();
    var div_table = '<p align="right">'+"\n"
      div_table += '<table id="my-ajax-table" class="table table-bordered table-hover">'+"\n"
      div_table += "\t"+'<thead>'+"\n"
      div_table += "\t"+"\t"+'<th data-dynatable-column="name">Terms</th>'+"\n"
      div_table += "\t"+"\t"+'<th id="score_column_id" data-dynatable-sorts="score" data-dynatable-column="score">Score</th>'+"\n"
      div_table += "\t"+"\t"+'</th>'+"\n"
      div_table += "\t"+'</thead>'+"\n"
      div_table += "\t"+'<tbody>'+"\n"
      div_table += "\t"+'</tbody>'+"\n"
      div_table += '</table>'+"\n"
      div_table += '</p>';
    $("#div-table").html(div_table)

    

    var div_stats = "<p>";
    for(var i in data.scores) {
      var value = (!isNaN(Number(data.scores[i])))? Number(data.scores[i]).toFixed(1) : data.scores[i];
      div_stats += i+": "+value+" | "
    }
    div_stats += "</p>"
    $("#stats").html(div_stats)


    for(var i in data.ngrams) {
    
      var le_ngram = data.ngrams[i]

      var orig_id = le_ngram.id
      var arr_id = parseInt(i)
      RecDict[orig_id] = arr_id;

      var node_info = {
        "id" : le_ngram.id,
        "name": le_ngram.name,
        "score": le_ngram.scores[FirstScore],//le_ngram.scores.tfidf_sum / le_ngram.scores.occ_uniq,
        "flag":false,
        "group_plus": true,
        "group_blocked": false,
        "state": (le_ngram.map)?1:0
      }
      AjaxRecords.push(node_info)

      if ( ! DistributionDict[node_info.score] ) DistributionDict[node_info.score] = 0;
      DistributionDict[node_info.score]++;
    }

    // console.log("The Distribution!:")
    // console.log(Distribution)
    var DistributionList = []
    var min_occ=99999,max_occ=-1,min_frec=99999,max_frec=-1;
    for(var i in DistributionDict) {
      var info = {
        "x_occ":Number(i),
        "y_frec":DistributionDict[i]
      }
      DistributionList.push(info)
      if(info.x_occ > max_occ) max_occ = info.x_occ
      if(info.x_occ < min_occ) min_occ = info.x_occ
      if(info.y_frec > max_frec) max_frec = info.y_frec
      if(info.y_frec < min_frec) min_frec = info.y_frec
    }

    oldest = Number(min_occ);
    latest = Number(max_occ);

    var ndx = false;
    ndx = crossfilter();
    ndx.add(DistributionList);

    // x_occs  = ndx.dimension(dc.pluck('x_occ'));
    var x_occs = ndx.dimension(function (d) {
        return d.x_occ;
    });

    var y_frecs = x_occs.group().reduceSum(function (d) {
        return d.y_frec;
    });

    console.log("scores: [ "+min_occ+" , "+max_occ+" ] ")
    console.log("frecs: [ "+min_frec+" , "+max_frec+" ] ")


    LineChart
      .width(800)
      .height(150)
      .margins({top: 10, right: 50, bottom: 25, left: 40})
      .group(y_frecs)
      .dimension(x_occs)
      .transitionDuration(500)
      .x(d3.scale.linear().domain([min_occ,max_occ+min_occ]))
      // .y(d3.scale.log().domain([min_frec/2,max_frec*2]))
      .renderArea(true)
      // .valueAccessor(function (d) {
      //     return d.value;
      // })
      
      // .stack(y_frecs, function (d) {
      //     return d.value;
      // })
      // .ordinalColors(d3.scale.category10())
      .elasticY(true)
      // .round(dc.round.floor)
      .renderHorizontalGridLines(true)
      .renderVerticalGridLines(true)
      // .colors('red')
      // .interpolate("monotone")
      // .renderDataPoints({radius: 2, fillOpacity: 0.8, strokeOpacity: 0.8})
      .brushOn(false)
      .title(function (d) {
                  var value = d.value.avg ? d.value.avg : d.value;
                  if (isNaN(value)) value = 0;
                  return value+" ngrams with "+FirstScore+"="+Number(d.key);
              })
      .xAxis();
    LineChart.yAxis().ticks(5)
    LineChart.render()


    volumeChart.width(800)
            .height(100)
            .margins({top: 30, right: 50, bottom: 20, left: 40})
            .dimension(x_occs)
            .group(y_frecs)
            .centerBar(true)
            .gap(5)
            .x(d3.scale.linear().domain([min_occ/2,max_occ+min_occ]))
            .y(d3.scale.sqrt().domain([min_frec/2,max_frec+min_frec]))
            // .elasticY(true)
            // // .round(d3.time.month.round)
            // // .xUnits(d3.time.months)
            .renderlet(function (chart) {
                chart.select("g.y").style("display", "none");
                LineChart.filter(chart.filter());
                console.log("lalaal moveChart.focus(chartfilt);")
            })
            .on("filtered", function (chart) {
                dc.events.trigger(function () {
                    var chartfilt = chart.filter()
                    // tricky part: identifying when the moveChart changes.
                    if(chartfilt) {
                        Push2Buffer ( chart.filter() )
                    } else {
                        if(TheBuffer) {
                            Push2Buffer ( false )
                        }
                    }
                    LineChart.focus(chartfilt);
                });
            })
            .xAxis()
      volumeChart.yAxis().ticks(5)
      volumeChart.render()

    LineChart.filterAll();
    volumeChart.filterAll();
    dc.redrawAll();

    MyTable = []
    MyTable = $('#my-ajax-table').dynatable({
                dataset: {
                  records: AjaxRecords
                },
                features: {
                  pushState: false,
                  // sort: false //i need to fix the sorting function... the current one just sucks
                },
                writers: {
                  _rowWriter: ulWriter
                  // _cellWriter: customCellWriter
                }
              })
              // .bind("dynatable:afterUpdate",  function(e, rows) {
              //   $(e.target).children("tbody").children().each(function(i) {
              //      $(this).click(function(){
              //        var row_nodeid = $(this).data('stuff')
              //        var elem = { "id":row_nodeid , "checked":false }
              //        overRide(elem); //Select one row -> select one ngram

              //       });
              //   });
              // });

    // MyTable.data('dynatable').settings.dataset.records = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = []
    // MyTable.data('dynatable').settings.dataset.originalRecords = AjaxRecords;
    
    MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').sorts.add('score', 0) // 1=ASCENDING,
    MyTable.data('dynatable').process();
    MyTable.data('dynatable').paginationPage.set(1);
    // MyTable.data('dynatable').process();
    // MyTable.data('dynatable').sorts.clear();
    MyTable.data('dynatable').process();

    // // // $("#score_column_id").children()[0].text = FirstScore
    // // // // MyTable.data('dynatable').process();

    if ( $(".imadiv").length>0 ) return 1;
    $('<br><br><div class="imadiv"></div>').insertAfter(".dynatable-per-page")
    $(".dynatable-record-count").insertAfter(".imadiv")
    $(".dynatable-pagination-links").insertAfter(".imadiv")



    var Div_PossibleActions = ""
    for(var action in PossibleActions) {
      var a = PossibleActions[action];
      var ischecked = (Number(action)==0)?"checked":"";
      Div_PossibleActions += '<input type="radio" id="radio'+action+'" name="radios" onclick="DeactivateSelectAll();" value="'+a.id+'" '+ischecked+'>';
      Div_PossibleActions += '<label style="color:'+a.color+';" for="radio'+action+'">'+a.name+'</label>';
    }
    var Div_SelectAll = ' <input type="checkbox" id="multiple_selection" onclick="SelectAll(this);" /> Select All'
    $(".imadiv").html('<div style="float: left; text-align:left;">'+Div_PossibleActions+Div_SelectAll+'</div><br>');


    return "OK"
}

function getIDFromURL( item ) {
	var pageurl = window.location.href.split("/")
	var cid;
	for(var i in pageurl) {
	    if(pageurl[i]==item) {
	        cid=parseInt(i);
	        break;
	    }
	} 
	return pageurl[cid+1];
}

// [ = = = = = = = = = = INIT = = = = = = = = = = ]
var corpus_id = getIDFromURL( "corpus" )
var url1=window.location.origin+"/api/node/"+corpus_id+"/ngrams/group",
	url2=window.location.origin+"/api/node/"+corpus_id+"/ngrams/keep",
	url3=window.location.href+"/ngrams.json";
var ngrams_groups, ngrams_map, ngrams_data;
$.when(
    $.ajax({
        type: "GET",
        url: url1,
        dataType: "json",
        success : function(data, textStatus, jqXHR) { ngrams_groups = data },
        error: function(exception) { 
            console.log("first ajax, exception!: "+exception.status)
        }
    }),
    $.ajax({
        type: "GET",
        url: url2,
        dataType: "json",
        success : function(data, textStatus, jqXHR) { ngrams_map = data },
        error: function(exception) { 
            console.log("first ajax, exception!: "+exception.status)
        }
    }),
    $.ajax({
        type: "GET",
        url: url3,
        dataType: "json",
        success : function(data, textStatus, jqXHR) { ngrams_data = data },
        error: function(exception) { 
            console.log("second ajax, exception!: "+exception.status)
        }
    })
).then(function() {

	// Deleting subforms from the ngrams-table, clean start baby!
    if( Object.keys(ngrams_groups.links).length>0 ) {

    	var _forms = {  "main":{} , "sub":{}  }
    	for(var i in ngrams_groups.links) {
    		_forms["main"][i] = true
    		for(var j in ngrams_groups.links[i]) {
    			_forms["sub"][ ngrams_groups.links[i][j] ] = true
    		}
    	}
    	var ngrams_data_ = []
    	for(var i in ngrams_data.ngrams) {
    		if(_forms["sub"][ngrams_data.ngrams[i].id]) {
    			ngrams_groups["nodes"][ngrams_data.ngrams[i].id] = ngrams_data.ngrams[i]
    		} else {
    			if( _forms["main"][ ngrams_data.ngrams[i].id ] )
    				ngrams_data.ngrams[i].name = "*"+ngrams_data.ngrams[i].name
    			ngrams_data_.push( ngrams_data.ngrams[i] )
    		}
    	}
    	ngrams_data.ngrams = ngrams_data_;
    }

    if( Object.keys(ngrams_map).length>0 ) {
    	for(var i in ngrams_data.ngrams) {
    		if(ngrams_map[ngrams_data.ngrams[i].id]) {
    			ngrams_data.ngrams[i]["map"] = true
    		}
    	}
    }


    // Building the Score-Selector
    var FirstScore = ngrams_data.scores.initial
    var possible_scores = Object.keys( ngrams_data.ngrams[0].scores );
    var scores_div = '<br><select style="font-size:25px;" class="span1" id="scores_selector">'+"\n";
    scores_div += "\t"+'<option value="'+FirstScore+'">'+FirstScore+'</option>'+"\n"
    for( var i in possible_scores ) {
      if(possible_scores[i]!=FirstScore) {
        scores_div += "\t"+'<option value="'+possible_scores[i]+'">'+possible_scores[i]+'</option>'+"\n"
      }
    }
    // Initializing the Charts and Table
    var result = Main_test( ngrams_data , FirstScore )
    console.log( result )

    // Listener for onchange Score-Selector
    scores_div += "<select>"+"\n";
    $("#ScoresBox").html(scores_div)
    $("#scores_selector").on('change', function() {
      console.log( this.value )
      var result = Main_test( ngrams_data , this.value )
      console.log( result )
    });


});