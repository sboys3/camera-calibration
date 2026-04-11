Shader "Unlit/FovCalibration"
{
	Properties
	{
		_FullScreen ("FullScreen", Float) = 1
		_TargetResolution ("TargetResolution", Vector) = (2048, 2048, 0, 0)
		_AlwaysDisplay ("AlwaysDisplay", Float) = 1
		[Enum(UnityEngine.Rendering.CompareFunction)] _ZTest ("ZTest", Int) = 4
		
		
		// _StencilRef ("Ref", Int) = 0
		// [Enum(UnityEngine.Rendering.CompareFunction)] _StencilComp ("Compare Function", Int) = 8
		// [Enum(UnityEngine.Rendering.StencilOp)] _StencilPassOp ("Pass Operation", Int) = 0
		// [Enum(UnityEngine.Rendering.StencilOp)] _StencilFailOp ("Fail Operation", Int) = 0
		// [Enum(UnityEngine.Rendering.StencilOp)] _StencilZFailOp ("ZFail Operation", Int) = 0
		// [Enum(UnityEngine.Rendering.StencilOp)] _StencilZFailOp ("ZFail Operation", Int) = 0
		// _StencilReadMask ("Read Mask", Int) = 255
		// _StencilWriteMask ("Write Mask", Int) = 255
	}
	SubShader
	{
		Tags { "RenderType"="Transparent" "Queue"="Overlay+900" "VRCFallback"="Hidden"}
		LOD 100
		Blend One OneMinusSrcAlpha
		ZWrite On
		// ZTest Always
		ZTest [_ZTest]
		Cull back
		
		// Stencil {
		// 	Ref [_StencilRef]
		// 	ReadMask [_StencilReadMask]
		// 	WriteMask [_StencilWriteMask]
		// 	Comp [_StencilComp]
		// 	Pass [_StencilPassOp]
		// 	Fail [_StencilFailOp]
		// 	ZFail [_StencilZFailOp]
		// }
		
		CGINCLUDE
		#pragma target 4.0
		ENDCG
		
		Pass
		{
			CGPROGRAM
			#pragma vertex vert
			#pragma fragment frag
			// make fog work
			#pragma multi_compile_fog

			#include "UnityCG.cginc"

			struct appdata
			{
				float4 vertex : POSITION;
				float2 uv : TEXCOORD0;
				uint id : SV_VertexID;
			};

			struct v2f
			{
				float2 uv : TEXCOORD0;
				float4 vertex : SV_POSITION;
				float4 clipPos : TEXCOORD1;
			};

			float _CameraCount;
			float _FullScreen;
			float2 _TargetResolution;
			float _AlwaysDisplay;
			
			float _VRChatCameraMode;

			v2f vert (appdata v)
			{
				v2f o;
				o.vertex = UnityObjectToClipPos(v.vertex);
				// o.clipPos = o.vertex;
				if(_FullScreen > 0){
					// overdraw
					#if defined(UNITY_REVERSED_Z)
					float closeZ = 0.999999;
					#else
					float closeZ = 0.000001;
					#endif
					o.vertex = float4((v.id < 2 ? -1 : 1), (v.id % 2 == 0 ? -1 : 1), closeZ, 1);
					// o.vertex = float4(((v.id == 0 || v.id == 3 ) ? -1 : 1), ((v.id == 2 || v.id == 3 ) ? 1 : -1), closeZ, 1);
					if(_FullScreen >= 2){
						// fit to screen
						float2 screenSize = _ScreenParams.xy;
						
						float2 offset = float2(0,0);
						float2 size = float2(0,0);
						
						// float minDim = min(screenSize.x, screenSize.y);
						
						bool isInVr = false;
						#if defined(USING_STEREO_MATRICES)
						isInVr = true;
						#endif
						
						bool maxDimIsX = screenSize.x / _TargetResolution.x > screenSize.y / _TargetResolution.y;
						if(screenSize.x < _TargetResolution.x || screenSize.y < _TargetResolution.y || isInVr){
							// scale and fit to screen
							float minScale = min(screenSize.x / _TargetResolution.x, screenSize.y / _TargetResolution.y);
							if(maxDimIsX){
								offset.x = -(screenSize.x - _TargetResolution.x * minScale);
							}else{
								offset.y = -(screenSize.y - _TargetResolution.y * minScale);
							}
							size = _TargetResolution * minScale;
						}else{
							// center on screen without scaling
							offset = -(screenSize - _TargetResolution);
							size = _TargetResolution;
						}
						//offset.y = screenSize.y - size.y;
						
						// apply scale and offset to vertex position
						offset = offset / screenSize;
						if(isInVr){
							// in vr so leave centered
							offset = 0;
						}
						size /= screenSize;
						o.vertex.xy *= size;
						o.vertex.xy += offset;
						if(isInVr){
							// in vr so place plane in front of camera
							o.vertex.z = -2;
							o.vertex.y *= -1;
							if(screenSize.x > screenSize.y){
								o.vertex.x *= screenSize.x / screenSize.y;
							}else{
								o.vertex.y *= screenSize.y / screenSize.x;
							}
							o.vertex.xyz *= 0.5;
							o.vertex.w = 1;
							// o.vertex = mul(UNITY_MATRIX_P, o.vertex);
							o.vertex = mul(UNITY_MATRIX_P, o.vertex);
						}
						if(_AlwaysDisplay == 0 && (_VRChatCameraMode < 1 || _VRChatCameraMode > 3)){
							// hide for main viewport
							o.vertex.xy = -2;
						}
					}
				}
				o.clipPos = o.vertex;
				o.uv = v.uv;//TRANSFORM_TEX(v.uv, _RenderTexture1);
				return o;
			}
			
			#include "./ShapeIntersections.cginc"
			
			// modulo that never returns negative values
			float modulo(float a, float b) {
				return a - floor(a / b) * b;
			}
			
			float3 HUEtoRGB(in float H){
				float R = abs(H * 6 - 3) - 1;
				float G = 2 - abs(H * 6 - 2);
				float B = 2 - abs(H * 6 - 4);
				return saturate(float3(R, G, B));
			}
			
			float3 HSVtoRGB(in float3 HSV){
				float3 RGB = HUEtoRGB(HSV.x);
				return ((RGB - 1) * HSV.y + 1) * HSV.z;
			}
			
			float4 frag (v2f i) : SV_Target
			{
				float2 uv = float2(i.uv.y, 1-i.uv.x);
				if(_FullScreen <= 0){
					uv = i.uv;
				}
				
				float3 viewSpaceViewDir = mul(inverse(UNITY_MATRIX_P), i.clipPos);
				// viewSpaceViewDir = normalize(mul(viewSpaceViewDir, (float3x3)UNITY_MATRIX_V));
				float4 col = float4(viewSpaceViewDir, 1);
				// return col;
				// col.r = 0;
				if(abs(viewSpaceViewDir.z - viewSpaceViewDir.x) < 0.01 || abs(viewSpaceViewDir.z - viewSpaceViewDir.y) < 0.01 || abs(viewSpaceViewDir.z + viewSpaceViewDir.x) < 0.01 || abs(viewSpaceViewDir.z + viewSpaceViewDir.y) < 0.01){
					// 90 degree angle
					// return 1;
				}
				float angleH = atan2(viewSpaceViewDir.x, -viewSpaceViewDir.z);
				float angleV = atan2(viewSpaceViewDir.y, -viewSpaceViewDir.z);
				angleH *= 180 / 3.1415926535897932384626433832795; // convert to degrees
				angleV *= 180 / 3.1415926535897932384626433832795; // convert to degrees
				// make the center 0,0
				// angleV = (angleV > 0) ? angleV - 180 : angleV + 180;
				// angleH = (angleH > 0) ? angleH - 180 : angleH + 180;
				// col.r = modulo(angleH, 1);
				// col.g = modulo(angleV, 1);
				col.r = angleH * 0.01;
				col.g = angleV * 0.01;
				col.b = 0;
				col.rgb = 0.1;
				
				float centerWidth = 0.1;
				if(abs(angleH) < centerWidth || abs(angleV) < centerWidth){
					col.rgb = 1;
				}
				
				float step = 5.0 / 2.0;
				float width = 0.05;
				float modH = modulo(angleH, step) / step;
				float modV = modulo(angleV, step) / step;
				float boxNumber = 0;
				if((modH <= width || modH >= 1 - width) && (abs(angleH) >= abs(angleV))){
					boxNumber = round(abs(angleH) / step);
				}
				if((modV <= width || modV >= 1 - width) && (abs(angleV) >= abs(angleH))){
					boxNumber = round(abs(angleV) / step);
				}
				
				if(boxNumber){
					col.rgb = HUEtoRGB(frac((boxNumber) * (1.0 / 6.0)));
					// col.rgb = boxNumber * 0.1;
				}
				
				// col.r = angleH / 3.1415926535897932384626433832795
				// col.r = angleH % 1.0f;
				// col.g = angleV;
				// col.b = 0;
				// col.r
				col.a = 0.9;
				if(_FullScreen <= 0 || _FullScreen >= 2){
					col.a = 1;
				}
				// col.rgb *= col.a;
				// if(abs(col0.r - uv.y) < 0.001){
				// 	col.rgb = 1;
				// }
				return col;
			}
			ENDCG
		}
	}
}
