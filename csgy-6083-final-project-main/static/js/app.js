function getClasses() {
  username = localStorage.getItem('username')
  var params = {"userName": username};

  const classes = sdk.userNameGet(params, {}, {})
    .then((res) => {
      if (res.status == 200) {
        return res.data;
      }
    }).catch( () => {
    console.log("failed");
    }
  )

  return classes;
}

function uploadFileToS3() {
  var file = document.getElementById('userFile').files[0];
  
  if (file) {
    // Read the file content as a binary data
    var reader = new FileReader();
    reader.onload = function (event) {
      // Convert the binary data to ArrayBuffer
      var fileData = event.target.result;
      var params = {
        "userName": 'ap2963',
        "courseName": 'csgy9223',
        "fileName": file.name
      };
      var additionalParams = {};

      var fileSizeInBytes = file.size;
      var fileSizeInMB = fileSizeInBytes / (1024 * 1024);
      console.log(fileSizeInMB);

      if (fileSizeInMB < 10) {
        sdk.userNameCourseNameFileNamePut(params, fileData, additionalParams)
          .then(function (res) {
            if (res.status == 200) {
              console.log(res.status);
            }
          }).catch(() => {
            console.log("upload failed");
          }
        );
      } else {
        // sdk GET bigfile
        sdk.userNameCourseNameBigFileFileNameGet(params, fileData, additionalParams)
          .then(function (res) {
            if (res.status == 200) {
              console.log(res.status);
              presignedURL = res.body;

              const uploadFile = async (presignedURL, fileData) => {
                const result = await Axios.put(presignedURL, fileData, {
                  headers: {
                    "x-api-key": 'wbv9kvsPu16Z7axKFfi7phdarNFuAGZ71y62Ilv1',
                    "Content-Type": "application/octet-stream"
                  }
                }).catch(
                
                 error => console.error(error.response.data, {request: error.request}));
            
                console.info(result.data);
                return result.data;
              };
            }
          }).catch(() => {
            console.log("big file upload failed");
          }
        );
      }}
    reader.readAsArrayBuffer(file);
  } else {
    console.error('No file selected.');
  }
}

function createNewClass() {
  var classLabel1Value = document.getElementById('classLabel1').value.trim();
  var classLabel2Value = document.getElementById('classLabel2').value.trim();

  if (!classLabel1Value || classLabel1Value.length === 0) {
    alert("You must provide a class title");
    return false;
  }

  if (divElement.textContent.trim().length > 0) 

  var params = {
    "userName": 'ap2963', 
    "className": classLabel1Value
  };

  sdk.userNameCreateCoursePost(params, {}, {})
    .then(function (result) {
      console.log('Folder created successfully:', result);
      alert("Success!");
    })
    .catch(function (error) {
      console.error('Error:', error);
      alert("Error");
    });
}

function displaySummary(text) {
  for (var i=0; i < text.length; i++) {
    if (text[i].length > 0) {
      var newSection = document.createElement('div');
      newSection.className = 'text-section';
      newSection.innerHTML = "<p>" + text[i] + "<p>"
      document.getElementById('summaryContainer').appendChild(newSection);
    }
  }
}

function getTextFile(path) {
  var request = new XMLHttpRequest();
  request.open('GET', path, true);
  request.send(null);
  request.onreadystatechange = function () {
    if (request.readyState === 4 && request.status === 200) {
      var type = request.getResponseHeader('Content-Type');
      if (type.indexOf("text") !== 1) {
        var outer_text = request.responseText;
        console.log(typeof(outer_text));
        outer_text = outer_text.split('\n'); 
        console.log(outer_text.length);
        console.log(outer_text[0]);
        displaySummary(outer_text);
      }
    }
  }
}

function getSummary(courseName, fileName) {
  const uName = localStorage.getItem('username');
  const cName = courseName;
  const fName = fileName;

  console.log(courseName)

  var params = {
    'userName': uName,
    'courseName': cName,
    'fileName': fName
  }

  sdk.userNameCourseNameFileNameGet(params, {}, {})
    .then((res) => {
      if (res.status == 200) {
        url = res.data['summary_url'];
        getTextFile(url);
      }
    }).catch( () => {
      console.log("failed");
    }
  );
}

function authenticateUser(params) {
  let data = new FormData()
  data.append("email", params['email'])
  data.append("password", params['password'])

  let fetchFormEncodedRequest = {
    method: "POST",
    mode: 'cors',
    body: data
  }

  fetch(
      '/loginAuth', 
      fetchFormEncodedRequest
  ).then(function(res) {
    if (res.status === 200) {
      res.json().then(function(data)
      {
        console.log(data);
        localStorage.setItem('userid', data['userid'])
        localStorage.setItem('email', data['email'])
        window.location.replace('./homepage.html')
      })
    }
  })
}

function registerUser(params) {
  let data = new FormData()
  data.append("fname", params['fname'])
  data.append("lname", params['lname'])
  data.append("email", params['email'])
  data.append("password", params['password'])
  data.append("street", params['street'])
  data.append("city", params['city'])
  data.append("state", params['state'])
  data.append("zipcode", params['zipcode'])

  let fetchFormEncodedRequest = {
    method: "POST",
    body: data
  }

  fetch('http://127.0.0.1:8000/registerUser', fetchFormEncodedRequest).then(function(res) {
    if (res.status === 200) {
      res.json().then(function(data)
      {
        console.log(data);
        localStorage.setItem('userid', data['userid']);
        window.location.replace('./home.html');
      })
    }
  })
}
function updateUser(params) {
  let data = new FormData();
  // Add all necessary fields for updating user details
  data.append("fname", params['fname']);
  data.append("lname", params['lname']);
  data.append("email", params['email']);
  data.append("password", params['password']);
  data.append("street", params['street']);
  data.append("city", params['city']);
  data.append("state", params['state']);
  data.append("zipcode", params['zipcode']);
  data.append("profileText", params['profileText']);
  data.append("photoUrl", params['photoUrl']);
  data.append("familyDetails", params['familyDetails']);

  let fetchFormEncodedRequest = {
    method: "POST",
    body: data
  };

  fetch('http://127.0.0.1:8000/edit-account-setting', fetchFormEncodedRequest)
  .then(function(res) {
    if (res.status === 200) {
      res.json().then(function(data) {
        console.log(data);
        localStorage.setItem('userid', data['userid']);
        window.location.replace('./homepage.html');  // Redirect to the user's dashboard
      })
    } else {
      res.json().then(function(data) {
        alert(data.message);  // Alert user of the error or other messages
      })
    }
  })
}

function getServiceLocationsForCustomer() {
  customerID = localStorage.getItem('customerID')

  let fetchFormEncodedRequest = {
    method: "POST",
  }

  fetch('http://127.0.0.1:8000/getServiceLocations?customerID=' + customerID, fetchFormEncodedRequest)
  .then((res) => {
    if (res.status == 200) {
      return res.json();
    }
  })
  .then(function(json) {
    return json;
  });
}

async function getDevicesForServiceLocation() {
  urlParams = new URLSearchParams(window.location.search)
  serviceLocID = urlParams.get('serviceLocID')

  let fetchFormEncodedRequest = {
    method: "POST",
  }

  const response = await fetch('http://127.0.0.1:8000/getDevices?serviceLocID=' + serviceLocID, fetchFormEncodedRequest);
  return await response.json();
}

function addDevicesToServiceLocation(params) {
  let data = new FormData()
  data.append("serviceLocID", params['serviceLocID'])
  data.append("deviceType", params['deviceType'])
  data.append("deviceModel", params['deviceType'])

  let fetchFormEncodedRequest = {
    method: "POST",
    body: data
  }

  fetch('http://127.0.0.1:8000/addDevice', fetchFormEncodedRequest).then(function(res) {
    if (res.status === 200) {
      res.json().then(function(data) {
        console.log(data)
        return data;
      });
    }
  });
}

function addServiceLocationToDB() {
  var street = document.getElementById('sl-street').value.trim();
  var unit = document.getElementById('sl-unit').value.trim();
  var city = document.getElementById('sl-city').value.trim();
  var state = document.getElementById('sl-state').value.trim();
  var zipCode = document.getElementById('sl-zipcode').value.trim();
  var dateTakenOver = document.getElementById('sl-dateTakenOver').value.trim();
  var squareFootage = document.getElementById('sl-squareFootage').value.trim();
  var numBedrooms = document.getElementById('sl-numBedrooms').value.trim();
  var numOccupants = document.getElementById('sl-numOccupants').value.trim();

  if (!classLabel1Value || classLabel1Value.length === 0) {
    alert("You must provide a class title");
    return false;
  }

  if (divElement.textContent.trim().length > 0) 

  var params = {
    "userName": 'ap2963', 
    "className": classLabel1Value
  };

  sdk.userNameCreateCoursePost(params, {}, {})
    .then(function (result) {
      console.log('Folder created successfully:', result);
      alert("Success!");
    })
    .catch(function (error) {
      console.error('Error:', error);
      alert("Error");
    });
}