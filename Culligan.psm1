
<#
	.Description
	Allow override of certificates. Use for local proxy testing
#>
Function Set-CertificatePolicyNoCheck
{
	add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@

	[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
}

<#
	.Description

	.Parameter

	.Example
#>
Function Template
{
	[CmdletBinding()]
	Param
	(
		[Parameter(Mandatory=$true, HelpMessage = "Help")]
		$Param
	)

	$FunctionName = "Template"

	$Method = "GET"
	$URI	= (Get-CulliganAPIUrl -Field "user-field") + "/users/sign_in.json"
	$ContentType = "application/json"
	$UserAgent	 = "Connect_Production/3.5.0 (iPhone; iOS 16.3.1; Scale/3.00)"
	$Body	= ""
	$Body 	= $Body | ConvertFrom-Json | ConvertTo-Json

	try
	{
		$response = Invoke-WebRequest -Uri $URI -Method $Method -ContentType $ContentType -UserAgent $UserAgent -Body $Body
	}
	catch
	{
		Write-Error "$FunctionName $_"
	}

	if($response)
	{
		$response = $response | ConvertFrom-Json
		return $response
	}
}

<#
	.Description
	Obtain a list of devices

	.Parameter CulliganToken
	Access token after logging in

	.Parameter DSN
	Properties says this is the WiFi module DSN

	.Example
#>
Function Get-CulliganProperties
{
	[CmdletBinding()]
	Param
	(
		[Parameter(Mandatory=$true, HelpMessage = "Access token after logging in")]
		$CulliganToken,

		[Parameter(Mandatory=$true, HelpMessage = "WiFi module DSN. Get from devices.json or properties.json")]
		$DSN
	)

	$FunctionName = "Get-CulliganProperties"

	$Method = "GET"
	$URI	= (Get-CulliganAPIUrl -Field "ads-field") + "/apiv1/dsns/$DSN/properties.json"
	$ContentType = "application/json"
	$UserAgent	 = "Connect_Production/3.5.0 (iPhone; iOS 16.3.1; Scale/3.00)"
	$Header		 = @{"Authorization" = "auth_token $CulliganToken"}

	try
	{
		$response = Invoke-WebRequest -Uri $URI -Method $Method -ContentType $ContentType -UserAgent $UserAgent -Headers $Header
	}
	catch
	{
		Write-Error "$FunctionName $_"
	}

	if($response)
	{
		$response = $response | ConvertFrom-Json
		return $response
	}
}

<#
	.Description
	Obtain a list of devices

	.Parameter CulliganToken
	Access token after logging in

	.Example
#>
Function Get-CulliganDevices
{
	[CmdletBinding()]
	Param
	(
		[Parameter(Mandatory=$true, HelpMessage = "Access token after logging in")]
		$CulliganToken
	)

	$FunctionName = "Get-CulliganDevices"

	$Method = "GET"
	$URI	= (Get-CulliganAPIUrl -Field "ads-field") + "/apiv1/devices.json"
	$ContentType = "application/json"
	$UserAgent	 = "Connect_Production/3.5.0 (iPhone; iOS 16.3.1; Scale/3.00)"
	$Header		 = @{"Authorization" = "auth_token $CulliganToken"}

	try
	{
		$response = Invoke-WebRequest -Uri $URI -Method $Method -ContentType $ContentType -UserAgent $UserAgent -Headers $Header
	}
	catch
	{
		Write-Error "$FunctionName $_"
	}

	if($response)
	{
		$response = $response | ConvertFrom-Json
		return $response
	}
}

<#
	.Description
	Obtain a new auth token

	.Parameter CulliganCred
	Username and password for Culligan account

	.Parameter AppSecret
	CWS-field app_secret. Looks like: CWS-field-{9}-{8}_{8}

	.Example
#>
Function Get-CulliganToken
{
	[CmdletBinding()]
	Param
	(
		[Parameter(Mandatory=$true, HelpMessage = "Username in email formet")]
		[PSCredential]$CulliganCred,

		[Parameter(Mandatory, HelpMessage = "app_secret")]
		[PSCredential]$AppSecret
	)

	$FunctionName = "Get-CulliganToken"

	$Method = "POST"
	$URI	= (Get-CulliganAPIUrl -Field "user-field") + "/users/sign_in.json"
	$ContentType = "application/json"
	$UserAgent	 = "Connect_Production/3.5.0 (iPhone; iOS 16.3.1; Scale/3.00)"
	$Body	= "{'user':{'email':'$($CulliganCred.username)','application':{'app_id':'CWS-field-id','app_secret':'$($AppSecret.getNetworkCredential().password)'},'password':'$($CulliganCred.getNetworkCredential().password)'}}"
	$Body 	= $Body | ConvertFrom-Json | ConvertTo-Json

	Write-Debug "$FunctionName : $URI, $Body"

	try
	{
		$response = Invoke-WebRequest -Uri $URI -Method $Method -ContentType $ContentType -UserAgent $UserAgent -Body $Body
	}
	catch
	{
		Write-Error "$FunctionName $_"
	}

	if($response)
	{
		$response = $response | ConvertFrom-Json
		return $response
	}
}

<#
	.Description
	Return the string of the server URL

	.Example
#>
Function Get-CulliganAPIUrl
{
	[CmdletBinding()]
	Param
	(
		[Parameter(Mandatory, HelpMessage = "Which API to call")]
		[ValidateSet("user-field","ads-field","metric-field")]$Field
	)

	$Server = "https://$($Field).aylanetworks.com"

	return $Server
}