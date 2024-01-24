#pragma rtGlobals=3		// Use modern global access method and strict wave access.


function give_labels(inputwave)
	wave inputwave
	variable labels
	variable number_of_labels
	variable i 
	string label_curr
	number_of_labels = DimSize(inputwave, 0)
	make /O /T /N = (number_of_labels) label_list	
	for(i=0; i<number_of_labels; i+=1)
		label_curr =  GetDimLabel(inputwave, 0, i)
		if (StringMatch(label_curr, "") == 1) 
			label_curr = "nan"
		endif
		print(label_curr)
		label_list[i] = label_curr
	endfor
End

//function apply_labels(labelswave, inputwave)
//	wave labelswave, inputwave
//	give_labels(labelswave)
	
//End