// Copyright Southern Spear. All Rights Reserved.

#include "SSServiceRanks.h"

#include "Engine/Texture2D.h"
#include "GameFramework/PlayerState.h"
#include "Net/UnrealNetwork.h"
#include "SSCoreLog.h"
#include "SSServiceLevelMath.h"
#include "TextureResource.h"

namespace
{
	const USSRankSettings& RankSettings()
	{
		return *GetDefault<USSRankSettings>();
	}
}

int64 FSSServiceRanks::XpForLevel(int32 Level)
{
	const USSRankSettings& S = RankSettings();
	return SSServiceLevelMath::XpForLevel(FMath::Clamp(Level, 1, FMath::Max(1, S.MaxLevel)), S.LevelXpScale, S.LevelXpExponent);
}

int32 FSSServiceRanks::LevelForXp(int64 Xp)
{
	const USSRankSettings& S = RankSettings();
	return SSServiceLevelMath::LevelForXp(Xp, S.LevelXpScale, S.LevelXpExponent, S.MaxLevel);
}

int32 FSSServiceRanks::RankIndexForLevel(int32 Level, TConstArrayView<FSSRankDefinition> Ranks)
{
	int32 Found = INDEX_NONE;
	for (int32 Index = 0; Index < Ranks.Num(); ++Index)
	{
		if (Level >= Ranks[Index].MinLevel && Level >= 1)
		{
			Found = Index;
		}
	}
	return Found;
}

const FSSRankDefinition* FSSServiceRanks::RankForLevel(int32 Level)
{
	const TArray<FSSRankDefinition>& Ranks = RankSettings().Ranks;
	const int32 Index = RankIndexForLevel(Level, Ranks);
	return Ranks.IsValidIndex(Index) ? &Ranks[Index] : nullptr;
}

bool FSSServiceRanks::Validate(TConstArrayView<FSSRankDefinition> Ranks, int32 MaxLevel, TArray<FString>& OutErrors)
{
	const int32 Before = OutErrors.Num();
	if (Ranks.Num() == 0)
	{
		OutErrors.Add(TEXT("The rank ladder is empty."));
		return false;
	}
	if (Ranks[0].MinLevel != 1)
	{
		OutErrors.Add(FString::Printf(TEXT("The first rank '%s' starts at level %d; it must start at 1."),
			*Ranks[0].Id.ToString(), Ranks[0].MinLevel));
	}
	TSet<FName> Seen;
	for (int32 Index = 0; Index < Ranks.Num(); ++Index)
	{
		const FSSRankDefinition& Rank = Ranks[Index];
		if (Rank.Id.IsNone())
		{
			OutErrors.Add(FString::Printf(TEXT("Rank %d has no Id."), Index));
		}
		else if (Seen.Contains(Rank.Id))
		{
			OutErrors.Add(FString::Printf(TEXT("Rank Id '%s' appears twice."), *Rank.Id.ToString()));
		}
		Seen.Add(Rank.Id);
		if (Rank.DisplayName.IsEmpty() || Rank.Abbreviation.IsEmpty())
		{
			OutErrors.Add(FString::Printf(TEXT("Rank '%s' needs a display name and an abbreviation."), *Rank.Id.ToString()));
		}
		if (Index > 0 && Rank.MinLevel <= Ranks[Index - 1].MinLevel)
		{
			OutErrors.Add(FString::Printf(TEXT("Rank '%s' (level %d) does not rise above '%s' (level %d)."),
				*Rank.Id.ToString(), Rank.MinLevel, *Ranks[Index - 1].Id.ToString(), Ranks[Index - 1].MinLevel));
		}
		if (Rank.MinLevel > MaxLevel)
		{
			OutErrors.Add(FString::Printf(TEXT("Rank '%s' starts at level %d, above MaxLevel %d; nobody could reach it."),
				*Rank.Id.ToString(), Rank.MinLevel, MaxLevel));
		}
	}
	return OutErrors.Num() == Before;
}

UTexture2D* FSSServiceRanks::InsigniaTexture(const FSSInsignia& Insignia)
{
	const SSInsigniaRaster::FSpec Spec = Insignia.ToSpec();
	if (SSInsigniaRaster::IsEmpty(Spec))
	{
		return nullptr;
	}
	static TMap<uint32, TWeakObjectPtr<UTexture2D>> Cache;
	const uint32 Key = uint32(FMath::Clamp(Spec.Chevrons, 0, 3)) | uint32(FMath::Clamp(Spec.Pips, 0, 3)) << 2
		| uint32(Spec.bCrown) << 4 | uint32(Spec.bCrest) << 5 | uint32(Spec.bSwordAndBaton) << 6;
	if (const TWeakObjectPtr<UTexture2D>* Found = Cache.Find(Key); Found && Found->IsValid())
	{
		return Found->Get();
	}

	constexpr int32 Size = 64;
	UTexture2D* Texture = UTexture2D::CreateTransient(Size, Size, PF_B8G8R8A8, *FString::Printf(TEXT("SS_Insignia_%u"), Key));
	if (!Texture)
	{
		return nullptr;
	}
	TArray<uint8> Alpha;
	Alpha.SetNumZeroed(Size * Size);
	SSInsigniaRaster::Rasterize(Spec, Size, Alpha.GetData());

	Texture->SRGB = true;
	Texture->Filter = TF_Bilinear;
	FTexture2DMipMap& Mip = Texture->GetPlatformData()->Mips[0];
	FColor* Pixels = static_cast<FColor*>(Mip.BulkData.Lock(LOCK_READ_WRITE));
	for (int32 Index = 0; Index < Size * Size; ++Index)
	{
		Pixels[Index] = FColor(255, 255, 255, Alpha[Index]);
	}
	Mip.BulkData.Unlock();
	Texture->UpdateResource();
	Texture->AddToRoot(); // shared by every scoreboard and menu for the session, like SSGlyphTextures
	Cache.Add(Key, Texture);
	return Texture;
}

USSServiceRankComponent::USSServiceRankComponent()
{
	SetIsReplicatedByDefault(true);
}

void USSServiceRankComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
	Super::GetLifetimeReplicatedProps(OutLifetimeProps);
	DOREPLIFETIME(USSServiceRankComponent, ServiceLevel);
}

void USSServiceRankComponent::SetServiceLevel(int32 Level)
{
	if (GetOwner() && GetOwner()->HasAuthority())
	{
		ServiceLevel = FMath::Clamp(Level, 0, FMath::Max(1, RankSettings().MaxLevel));
	}
}

USSServiceRankComponent* USSServiceRankComponent::FindOrAdd(APlayerState* PlayerState)
{
	if (!PlayerState || !PlayerState->HasAuthority())
	{
		return nullptr;
	}
	if (USSServiceRankComponent* Existing = PlayerState->FindComponentByClass<USSServiceRankComponent>())
	{
		return Existing;
	}
	USSServiceRankComponent* Component = NewObject<USSServiceRankComponent>(PlayerState, TEXT("SSServiceRank"));
	Component->RegisterComponent();
	return Component;
}
