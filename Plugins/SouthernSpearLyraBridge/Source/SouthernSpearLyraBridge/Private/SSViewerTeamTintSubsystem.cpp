// Copyright Southern Spear. All Rights Reserved.

#include "SSViewerTeamTintSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "SSTeamIdentityLibrary.h"
#include "SSLocalityPresentable.h"
#include "Components/MeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Misc/Paths.h"
#include "Teams/LyraTeamSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogSSBridge, Log, All);

IMPLEMENT_MODULE(FDefaultModuleImpl, SouthernSpearLyraBridge)

namespace
{
	// Southern Spear palette (Site/styles.css): sage friendly, OPFOR clay opposing.
	FLinearColor Srgb(const TCHAR* Hex) { return FLinearColor::FromSRGBColor(FColor::FromHex(Hex)); }

	// Lyra's shooter teams use generic ids 1 and 2 (same mapping as the objective director).
	ESSTeamId ToTeamId(int32 LyraTeamId)
	{
		return LyraTeamId == 1 ? ESSTeamId::TeamOne : LyraTeamId == 2 ? ESSTeamId::TeamTwo : ESSTeamId::None;
	}

	// The colour parameters Lyra's team display assets drive (TeamDA_*). Set
	// directly because ULyraTeamDisplayAsset is not exported from LyraGame.
	const FName BaseParams[] = { TEXT("TeamColor") };
	const FName GlowParams[] = { TEXT("EdgeGlowColor"), TEXT("EmissiveColor"), TEXT("EmissiveColor2"), TEXT("EmissiveColor3") };

	/**
	 * Held weapon, viewer-relative (ADR-016 W-101/W-102; producer: "the OPFOR need to be MAF"): to this viewer a
	 * soldier on the other side carries the MAF counterpart of his A-series weapon - same gameplay definition,
	 * different display mesh (Tools/Unreal/setup_maf_weapons.py). The A-series mesh is remembered in a component
	 * tag and restored if the soldier reads as friendly again. Pistols keep their mesh (no counterpart yet).
	 */
	void SwapHeldWeapon(AActor* Weapon, ESSLocality Locality)
	{
		static const FString OriginalTag = TEXT("SSOriginalMesh:");
		TInlineComponentArray<UStaticMeshComponent*> Visuals(Weapon);
		for (UStaticMeshComponent* Visual : Visuals)
		{
			UStaticMesh* Current = Visual->GetStaticMesh();
			if (!Current || !Current->FindSocket(TEXT("Muzzle")))
			{
				continue;
			}
			FString OriginalPath;
			for (const FName& Tag : Visual->ComponentTags)
			{
				if (Tag.ToString().StartsWith(OriginalTag))
				{
					OriginalPath = Tag.ToString().Mid(OriginalTag.Len());
				}
			}
			const FString Name = OriginalPath.IsEmpty() ? Current->GetName() : FPaths::GetBaseFilename(OriginalPath);
			if (Locality == ESSLocality::Opposing)
			{
				if (!Name.StartsWith(TEXT("SM_A")) || Name.StartsWith(TEXT("SM_A9")))
				{
					continue;
				}
				const bool bSupport = Name.StartsWith(TEXT("SM_A89"));
				static TWeakObjectPtr<UStaticMesh> Rifle, Support;
				TWeakObjectPtr<UStaticMesh>& Counterpart = bSupport ? Support : Rifle;
				if (!Counterpart.IsValid())
				{
					Counterpart = LoadObject<UStaticMesh>(nullptr, bSupport
						? TEXT("/SSExp_ObjectiveAssault/Weapons/MAF/SM_MAF_S1.SM_MAF_S1") : TEXT("/SSExp_ObjectiveAssault/Weapons/MAF/SM_MAF_R1.SM_MAF_R1"));
				}
				if (Counterpart.IsValid() && Current != Counterpart.Get())
				{
					if (OriginalPath.IsEmpty())
					{
						Visual->ComponentTags.Add(FName(OriginalTag + Current->GetPathName()));
					}
					Visual->SetStaticMesh(Counterpart.Get());
				}
			}
			else if (!OriginalPath.IsEmpty() && Current->GetPathName() != OriginalPath)
			{
				if (UStaticMesh* Original = LoadObject<UStaticMesh>(nullptr, *OriginalPath))
				{
					Visual->SetStaticMesh(Original);
				}
			}
		}
	}

	void Tint(AActor* Actor, const FLinearColor& Base, const FLinearColor& Glow, ESSLocality Locality)
	{
		TArray<AActor*> Actors { Actor };
		Actor->GetAttachedActors(Actors, /*bResetArray=*/ false, /*bRecursivelyIncludeAttachedActors=*/ true);
		for (AActor* Each : Actors)
		{
			// Viewer-relative looks (3 ACR / MAF soldier bodies).
			if (ISSLocalityPresentable* Presentable = Cast<ISSLocalityPresentable>(Each))
			{
				Presentable->ApplyViewerLocality(Locality);
			}
			if (Each != Actor)
			{
				SwapHeldWeapon(Each, Locality);
			}
			TInlineComponentArray<UMeshComponent*> Meshes(Each);
			for (UMeshComponent* Mesh : Meshes)
			{
				for (const FName& Name : BaseParams) { Mesh->SetVectorParameterValueOnMaterials(Name, FVector(Base)); }
				for (const FName& Name : GlowParams) { Mesh->SetVectorParameterValueOnMaterials(Name, FVector(Glow)); }
			}
		}
	}
}

bool USSViewerTeamTintSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->GetNetMode() != NM_DedicatedServer && Super::ShouldCreateSubsystem(Outer);
}

bool USSViewerTeamTintSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

TStatId USSViewerTeamTintSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(USSViewerTeamTintSubsystem, STATGROUP_Tickables);
}

void USSViewerTeamTintSubsystem::Tick(float DeltaTime)
{
	// Lyra re-applies its own colours on team/pawn changes; a frequent, cheap
	// re-apply (parameter sets only) keeps the viewer-relative tint on top.
	Accumulator += DeltaTime;
	if (Accumulator < 0.5f)
	{
		return;
	}
	Accumulator = 0.f;

	UWorld* World = GetWorld();
	const APlayerController* Viewer = World ? World->GetFirstPlayerController() : nullptr;
	ULyraTeamSubsystem* Teams = World ? World->GetSubsystem<ULyraTeamSubsystem>() : nullptr;
	if (!Viewer || !Viewer->IsLocalController() || !Teams)
	{
		return;
	}
	const ESSTeamId ViewerTeam = ToTeamId(Teams->FindTeamFromObject(Viewer));
	if (!FSSTeamIdentity::IsPlayableTeam(ViewerTeam))
	{
		return; // no authorised vantage: leave Lyra's absolute colours
	}

	LastTintedCount = 0;
	for (TActorIterator<APawn> It(World); It; ++It)
	{
		const ESSTeamId Subject = ToTeamId(Teams->FindTeamFromObject(*It));
		if (!FSSTeamIdentity::IsPlayableTeam(Subject))
		{
			continue;
		}
		const FSSLocalityResolution Resolution = FSSTeamIdentity::ResolveLocality(ViewerTeam, Subject);
		if (!Resolution.IsResolved())
		{
			continue;
		}
		static const FLinearColor FriendlyBase = Srgb(TEXT("B9C1B4")), FriendlyGlow = Srgb(TEXT("D6E2CF"));
		static const FLinearColor OpposingBase = Srgb(TEXT("8C493D")), OpposingGlow = Srgb(TEXT("C98A7C"));
		const bool bFriendly = Resolution.Locality == ESSLocality::Friendly;
		Tint(*It, bFriendly ? FriendlyBase : OpposingBase, bFriendly ? FriendlyGlow : OpposingGlow, Resolution.Locality);
		++LastTintedCount;
	}
	if (LastTintedCount != LastLoggedCount)
	{
		LastLoggedCount = LastTintedCount;
		UE_LOG(LogSSBridge, Log, TEXT("Viewer-relative tint applied to %d pawn(s) (viewer %s)."),
			LastTintedCount, *FSSTeamIdentity::ToDebugString(ViewerTeam));
	}
}
