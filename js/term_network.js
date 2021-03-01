$("#mynetwork").empty();

var tsv;

function load_data(){
data = $("#target_data").val();
tsv = data.replace(/\|\|/g,"\t").replace(/%%/g,"\n");
target = $("#target_word").val();
render(target);
}

function render(target){
	if (target==null){
		target=$("#entity_term").val();
	}
var node_data = {};
var id_mapping = {};
var edge_data = {};

max_id = 1;
thresh=50;  // retrieve top 50 phrases
let counter = 0;

lines = tsv.split("\n");
for (line of lines){
	if (counter>thresh){
		break;
	}
	if (line.includes("\t")){
		fields = line.split("\t");
		if (fields[1] == target){
			counter++;
			words = fields[2].split(" ");
			if (words.length>6 ){  
				words = words.slice(0,6);
				if (!(words.includes(target + '_0_node'))){
					continue;
				}
				//words.push("...");
			}
			freq = parseInt(fields[3]);
			current_words = [];
			prev_word = "";
			increment = 1;
			for (word of words){
				if (current_words.includes(word)){
						word = word + "_"+ increment.toString();
					increment++;
				}
				current_words.push(word);
				if (!(word in node_data)){
					node_data[word] = 0;
					id_mapping[word] = max_id;
					max_id++;
				}
				node_data[word] += freq;
				if (prev_word!=""){
					if  (!(prev_word in edge_data)){
						edge_data[prev_word] ={};
					}
					if  (!(word in edge_data[prev_word])){
						edge_data[prev_word][word] =0;
					}
					edge_data[prev_word][word] +=1;
				}
				prev_word = word;
			}
		}
	}
}

var nodes = null;
var edges = null;
var network = null;

function draw(node_data, edge_data,id_mapping, target) {

/*  nodes = [
    { id: 1, value: 20, label: "ⲡ" },
    { id: 2, value: 15, label: "ⲟⲩ" },
    { id: 3, value: 35, label: "ⲣⲱⲙⲉ" },
    { id: 4, value: 35, label: "ⲛ" },
    { id: 5, value: 22, label: "ⲁⲅⲁⲑⲟⲥ" },
    { id: 6, value: 13, label: "ⲡⲟⲛⲏⲣⲟⲥ" },
  ];*/

nodes=[];
id2node = {};
for (d in node_data){
	word =  d.replace(/_.*/g,'');
	freq = node_data[d];
	
	if (word==target){
		node = {id: id_mapping[d], value: freq, label: word, color:"#ec325d", border: "red" };
	}
	else{
		node = {id: id_mapping[d], value: freq, label: word };	
	}
	//if (freq>1){
		nodes.push(node);
		id2node[node.id] = node;
		console.log(node);
	//}
}

  // create connections between people
  // value corresponds with the amount of contact between two people
  edges = [
    { from: 1, to: 3, value: 20, arrows: "to"},
    { from: 2, to: 3, value: 15, arrows: "to" },
    { from: 3, to: 4, value: 35, arrows: "to" },
    { from: 4, to: 5, value: 22, arrows: "to" },
    { from: 4, to: 6, value: 13, arrows: "to"}
  ];

edges = [];
source_count = {};
for (word in edge_data){
	w1 = id_mapping[word];
	if (!(w1 in source_count)){source_count[w1]=0.0;}
	for (next_word in edge_data[word]){
		w2 = id_mapping[next_word];
		freq = edge_data[word][next_word];
		
		round_val = 0.2*source_count[w1];
		if (round_val>1){round_val = 1.0;}
		edge = {from: w1, to: w2, value: freq, arrows:"to",color:"#08c", "smooth": {"type": 'curvedCW', "roundness": round_val, "forceDirection": "none"}};
		//if (freq >1){
			//if (w1 in id2node && w2 in id2node){
				edges.push(edge);
			//}
		//}
		console.log(edge);
		source_count[w1]++;
	}
}




  // Instantiate our network object.
  var container = document.getElementById("mynetwork");
  var data = {
    nodes: nodes,
    edges: edges
  };
  var options = {
	  layout: {
  hierarchical: {
    direction: "LR",
    sortMethod: "directed"
  }
},
    nodes: {
      shape: "dot",
	  font: {    size: 25    },
      scaling: {
        customScalingFunction: function(min, max, total, value) {
          return value / total;
        },
        min: 5,
        max: 150
      }
    }
  };
  network = new vis.Network(container, data, options);
}


/*window.addEventListener("load", () => {
  draw();
});*/
  draw(node_data, edge_data,id_mapping,target);
  
}

