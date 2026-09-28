// Copyright Southern Spear. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"

/**
 * Small UI shapes built at runtime (the UI fonts, Barlow Condensed and Inter, have no triangle glyph:
 * a "▲" text arrow rendered as nothing). White, so widgets tint them.
 */
namespace SSGlyphTextures
{
	/** A 64 px white triangle pointing up, anti-aliased, transparent elsewhere. */
	inline UTexture2D* Triangle()
	{
		static TWeakObjectPtr<UTexture2D> Cache;
		if (Cache.IsValid())
		{
			return Cache.Get();
		}
		constexpr int32 Size = 64;
		UTexture2D* Texture = UTexture2D::CreateTransient(Size, Size, PF_B8G8R8A8, TEXT("SS_GlyphTriangle"));
		if (!Texture)
		{
			return nullptr;
		}
		Texture->SRGB = true;
		Texture->Filter = TF_Bilinear;
		FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
		FColor* Pixels = static_cast<FColor*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
		// Apex (32, 4), base from (6, 58) to (58, 58); 4x4 supersampling for the edges.
		const FVector2D A(32.f, 4.f), B(58.f, 58.f), C(6.f, 58.f);
		auto Edge = [](const FVector2D& P, const FVector2D& From, const FVector2D& To)
		{
			return (To.X - From.X) * (P.Y - From.Y) - (To.Y - From.Y) * (P.X - From.X);
		};
		for (int32 Y = 0; Y < Size; ++Y)
		{
			for (int32 X = 0; X < Size; ++X)
			{
				int32 Inside = 0;
				for (int32 S = 0; S < 16; ++S)
				{
					const FVector2D P(X + (S % 4 + 0.5f) / 4.f, Y + (S / 4 + 0.5f) / 4.f);
					Inside += (Edge(P, A, B) >= 0.f && Edge(P, B, C) >= 0.f && Edge(P, C, A) >= 0.f) ? 1 : 0;
				}
				Pixels[Y * Size + X] = FColor(255, 255, 255, static_cast<uint8>(Inside * 255 / 16));
			}
		}
		Mip.BulkData.Unlock();
		Texture->UpdateResource();
		Texture->AddToRoot(); // shared by every HUD for the session
		Cache = Texture;
		return Texture;
	}

	/** A 512 px scope eyepiece mask: black outside a circle, clear inside, with a soft dark rim (the tube). */
	inline UTexture2D* ScopeMask()
	{
		static TWeakObjectPtr<UTexture2D> Cache;
		if (Cache.IsValid())
		{
			return Cache.Get();
		}
		constexpr int32 Size = 512;
		UTexture2D* Texture = UTexture2D::CreateTransient(Size, Size, PF_B8G8R8A8, TEXT("SS_GlyphScopeMask"));
		if (!Texture)
		{
			return nullptr;
		}
		Texture->SRGB = true;
		Texture->Filter = TF_Bilinear;
		FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
		FColor* Pixels = static_cast<FColor*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
		const float Radius = Size * 0.5f - 2.f;
		for (int32 Y = 0; Y < Size; ++Y)
		{
			for (int32 X = 0; X < Size; ++X)
			{
				const float D = FVector2f(X + 0.5f - Size * 0.5f, Y + 0.5f - Size * 0.5f).Size() / Radius; // 1 at the edge
				// Clear centre, darkening over the outer 12% (the tube), opaque past the edge.
				const float Alpha = FMath::Clamp((D - 0.88f) / 0.12f, 0.f, 1.f);
				Pixels[Y * Size + X] = FColor(0, 0, 0, static_cast<uint8>(FMath::Square(Alpha) * 255.f));
			}
		}
		Mip.BulkData.Unlock();
		Texture->UpdateResource();
		Texture->AddToRoot();
		Cache = Texture;
		return Texture;
	}
}
